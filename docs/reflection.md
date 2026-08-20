# Reflektionsdokument – obligatorisk leverabel

###1. Varför ska sensorerna kommunicera med ett API i stället för direkt med PostgreSQL?
Rollen ett API spelar i en arkitektur är att vara en agnostisk mellanhand som gör att olika applikationer eller 
arkitekturdelar, i det här fallet sensorer och en databas, kan utbyta information. Med det här upplägget följer en rad fördelar
gällande säkerhet (dem enskilda sensorerna behöver inte ha access till databasen och utgöra eventuella ingresser på nätverket), validering 
av inkommande data (som i den här laborationen utgörs av bl.a. funktionerna device_exists och validate_measurement) tillförd abstraktion (sensorerna
är helt omedvetna om SQL-databasen varför den kan bytas ut och enbart db.py skulle behöva skrivas om/ändras), resurshantering på nätverket (connection pooling hindrar att databasen kraschar av för många enskilda anslutningar) och strömlinjeformning av protokoll (basal hårdvara som sensorer eller MCU är inte lämpade att upprätthålla databasanslutningar utan brukar funkar bäst när dem skickar POST eller GET som i simulator.py).

---
 
####2. Varför ska felaktig sensordata stoppas innan den sparas?
Det är viktigt av flera skäl att stoppa felaktig sensordata innan den lagras i databasen. Felaktiga värden med kraftiga svängningar i t.ex. temperatur (tänk minusgrader i ett växthus eller plusgrader i ett frysrum) korrumperar helhetsbilden av miljön som sensorerna är satta att kontrollera eftersom historiken av mätningar utgörs av data som de facto inte reflekterar verkliga upptag. I den här laborationen implementeras inga spärrar eller larm för svängningar i temp eller luftfuktighet (som vi implementerade i jensen-datapipeline) däremot används validering av datatyper, återigen via validate_measurements, och åtkomstbegräningsning i form av tre sensorer. Typvalideringen avhjälper att att databasen riskerar att krascha när den förväntas lagra exempelvis strängar för ett tempvärde istället för floats eller tomma inserts från en sensor som hängt sig och inte längre skickar några värden. Som en bonus skyddar det även mot sql-injektioner, även om dem kanske inte är lika vanliga idag som när det begav sig.

---

###3. Varför passar PostgreSQL för historiska mätvärden?
I första hand skulle jag vilja säga på grund av det enkla faktumet att det har persistens, alltså att det lagras på hårddisk och inte lever i RAM. Ska
du avläsa en graf för en månads mätningar exempelvis hade det varit både extremt dyrt och volatilt att ha det i arbetsminnet i det fall att processen kraschar. På andras sidan myntet har vi cachen (i form av redis i laborationen) som sparas i RAM men används för enskilda rader som kan tillgås mycket snabbare utan att SQL behöver belastas via en connection.

---
 
###4. Vad händer med lösningen om Redis försvinner?
För att återknyta till det förra svaret så är redis roll i arkitekturen att snabbt leverera ett värde utan att API skapar en ny connection till databasen. Om Redis kraschar faller alltså lösningen tillbaks på att prata med databasen direkt vilket leder till långsammare respons och mer belastning av PostgresSQL. 

---

###5. Vad händer med lösningen om PostgreSQL försvinner?
Om databasen går ner är det ett kritiskt fel för hela lösningen eftersom den är källan till avläsningar som tillgås via GET /meaurements och införing av sensordata via POST. Redis slutar också fungera eftersom att det här beror av den returnerade raden från insert_measurement i app.py. Man kan såklart fortfarande läsa av sensorerna interaktivt i loggarna men det är knappast tillfredställande för den här typen av lösningar eftersom det inte är en geigermätare.

---
 
###6. Varför används Docker Compose lokalt?
Om jag tolkar frågan rätt så används docker här lokalt i kontrast till att imagen laddas upp på github för deployment i cloud som i övningen jensenstore-api för att detta är tänkt att representera en utvecklingsmiljö som inte är färdig för produktion som det senare är avsett för. Lösningen utgörs dessutom av flera containers som pratar med varandra internt via docker och en webbläsare via host port på jensen-iot-lab-api, alltså är det tänkt att köras i ett slutet system. Eftersom laborationen också utförs via kodändringar i bl.a. app.py och db.py måste dem avspeglas varje gång man kör compose lokalt.

---

###7. Vad automatiserar din CI-pipeline?
I pipelinen automatiseras testning av koden i repot. Om man tittar på stegen i Actions så spinner den först upp en virtuell maskin (i det här fallet körande ubuntu 24.04) som runner, sedan gör den en checkout för att hämta koden i som lagts upp (i det här fallet app.py, db.py etc), det tredje steget är att installera python enligt specifierad version i ci.yml, därefter adderar den till pythonmiljön genom att installera modulerna som specifieras i api/requirements.txt via pip, därefter körs testerna av validate_measurements som radas upp i api/tests/test_validation.py, steg fem är att bygga dockerimagen som defineras i ci.yml och slutligen körs post-run actions och cleanups som reverserar tidigare steg och städar bort orphan processes. Lägger man på även continous delivery så sätts också docker imagen i produktion via en container, exempelvis i cloud eller på en VPS.

---

###8. Vad observerade du när du tog bort en Kubernetes Pod?
När man kör kubectl delete pod fryser terminalen vilket i sig gör det svårt att ta ner flera podar inom ett kort tidsspektrum. Men oavsett det har minikube inbyggd automatik för självläkning som utgår ifrån desired state som defineras av /k8s/deployment.yml, i det här fallet ska 3 repliker av dockerimagen köras i 3 podar. En replica-set-controller kontrollerar hela tiden om antalet podar som körs motsvarar desired state och agerar blixtsnabbt om  någon i klustret kraschar eller tas bort. Därtill används också graceful termination som gör att poden stängs ner långsamt. Kontentan och det man ser när man kör kubectl get pods -w i en annan terminal är alltså att poden man tar bort inte försvinner direkt och att en ny sätts i spel direkt när man skickat delete.

---

###9. Varför kan flera repliker ge högre tillgänglighet?
Flera podar kan hantera en större trafikmängd och load balancing dem emellan säkerställer att dem alla tar emot en hanterbar mängd anslutningar istället för att flera är idle men en tar hela smällen. Det bygger även in redundans och robusthet mot krascher. 

---

###10. När hade Kubernetes varit overkill för en lösning?
Bilden jag har fått som sannerligen inte bygger på någon extensiv erfarenhet av devOps är att orkestrering främst lämpar sig för system med stor variation av trafikflöden som till exempel säsongsbetonad försäljning eller planerade trafiktoppar. Ett system som illustreras av labben vi precis har gjort omfattas inte alls av det, det är inte någon risk att det helt plötsligt ansluts fler sensorer till systemet liksom och måste hanteras av flera repliker av API. I det fallet innebär kubernetes bara onödig overhead och utökad komplexitet.



