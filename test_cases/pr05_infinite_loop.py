def find_item(items, target):
    index = 0
    while True:
        if items[index] == target:
            return index
        index += 1
