import json
import os
import redis

client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
)


def get_latest_from_cache(device_id):


    key = f"latest:{device_id}"

    value = client.get(key)

    if value is None:
        return None

    return json.loads(value)

    return None

def set_latest_in_cache(device_id, measurement):


    key = f"latest:{device_id}"
    try:
        json_data = json.dumps(measurement)
        client.set(key, json_data)
        print(f"SUCCESS:  sparade {device_id} i redis cachen!", flush=True)
    except Exception as e:
        print(f"ERROR i set_latest_in_cache för {device_id}: {e}", flush=True)
    
    pass
