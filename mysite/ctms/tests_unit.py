from ctms.views import pagination


def test_pagination():
    pages = 24
    assert pagination(pages, 1) == [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), ('...', 4)]
    assert pagination(pages, 2) == [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), ('...', 5)]
    assert pagination(pages, 3) == [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), ('...', 6)]
    assert pagination(pages, 4) == [('...', 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), ('...', 7)]
    assert pagination(pages, 5) == [('...', 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), ('...', 8)]
    assert pagination(pages, 6) == [('...', 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), ('...', 9)]
    assert pagination(pages, 7) == [('...', 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), ('...', 10)]
    assert pagination(pages, 8) == [('...', 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), ('...', 11)]
    assert pagination(pages, 9) == [('...', 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), ('...', 12)]
    assert pagination(pages, 10) == [('...', 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12), ('...', 13)]
    assert pagination(pages, 11) == [('...', 8), (9, 9), (10, 10), (11, 11), (12, 12), (13, 13), ('...', 14)]
    assert pagination(pages, 12) == [('...', 9), (10, 10), (11, 11), (12, 12), (13, 13), (14, 14), ('...', 15)]
    assert pagination(pages, 13) == [('...', 10), (11, 11), (12, 12), (13, 13), (14, 14), (15, 15), ('...', 16)]
    assert pagination(pages, 14) == [('...', 11), (12, 12), (13, 13), (14, 14), (15, 15), (16, 16), ('...', 17)]
    assert pagination(pages, 15) == [('...', 12), (13, 13), (14, 14), (15, 15), (16, 16), (17, 17), ('...', 18)]
    assert pagination(pages, 16) == [('...', 13), (14, 14), (15, 15), (16, 16), (17, 17), (18, 18), ('...', 19)]
    assert pagination(pages, 17) == [('...', 14), (15, 15), (16, 16), (17, 17), (18, 18), (19, 19), ('...', 20)]
    assert pagination(pages, 18) == [('...', 15), (16, 16), (17, 17), (18, 18), (19, 19), (20, 20), ('...', 21)]
    assert pagination(pages, 19) == [('...', 16), (17, 17), (18, 18), (19, 19), (20, 20), (21, 21), ('...', 22)]
    assert pagination(pages, 20) == [('...', 17), (18, 18), (19, 19), (20, 20), (21, 21), (22, 22), ('...', 23)]
    assert pagination(pages, 21) == [('...', 18), (19, 19), (20, 20), (21, 21), (22, 22), (23, 23), ('...', 24)]
    assert pagination(pages, 22) == [('...', 19), (19, 19), (20, 20), (21, 21), (22, 22), (23, 23), (24, 24)]
    assert pagination(pages, 23) == [('...', 20), (19, 19), (20, 20), (21, 21), (22, 22), (23, 23), (24, 24)]
    assert pagination(pages, 24) == [('...', 21), (19, 19), (20, 20), (21, 21), (22, 22), (23, 23), (24, 24)]
    pages = 3
    assert pagination(pages, 1) == [(1, 1), (2, 2), (3, 3)]
    assert pagination(pages, 2) == [(1, 1), (2, 2), (3, 3)]
    assert pagination(pages, 3) == [(1, 1), (2, 2), (3, 3)]