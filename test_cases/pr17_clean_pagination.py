def paginate(items: list, page: int, page_size: int = 10) -> list:
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be positive")
    start = (page - 1) * page_size
    return items[start : start + page_size]
