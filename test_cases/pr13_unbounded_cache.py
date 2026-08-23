cache = {}

def process_request(request_id, data):
    result = data * 2
    cache[request_id] = result
    return result
