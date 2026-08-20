# Jensen IoT Platform – slutlaboration för IOT25M\_DTA 

---

## SQL-frågorna som specififerades i labbguiden.

### 1. Räkna totalt antal mätningar
Den här frågan returnerar det totala antalet rader av measurements i tabellen, kan användas för att utvärdera att datan lagras som den ska.
```sql
SELECT COUNT(*) FROM measurements;
```

### 2. Beräkna genomsnittligt mätvärde
Den här frågan räknar ut medelvärdet för en specifik kolumn (exempelvis temperatur eller luftfuktighet) för alla sparade mätningar. Den är användbar för att snabbt se att sensorernas samlade data ligger på en rimlig och förväntad nivå.
```sql
SELECT AVG(value) FROM measurements;
```

### 3. Hämta data från de senaste 24 timmarna
Den här frågan filtrerar tabellen och returnerar endast de mätningar som har registrerats under det senaste dygnet, för att användas i exempelvis en graf eller dashboard.
```sql
SELECT * FROM measurements
WHERE created_at >= NOW() - INTERVAL '24 hours';
```

### av: Jeremias Mikaelsson IOT25M

