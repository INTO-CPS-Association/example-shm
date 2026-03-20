from record import replay

def replay_mqtt(config_path):
    replay.replay_mqtt_messages(config_path, loop=10)
