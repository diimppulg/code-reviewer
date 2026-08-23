import threading

counter = 0

def increment():
    global counter
    current = counter
    current += 1
    counter = current

threads = [threading.Thread(target=increment) for _ in range(100)]
for thread in threads:
    thread.start()
