from record import replay, record
from record.replay import LOOPS

def record_mqtt(config_path):
    record.record_mqtt(config_path)

def replay_mqtt(config_path):
    replay.replay_mqtt_messages(config_path, loop=LOOPS)
