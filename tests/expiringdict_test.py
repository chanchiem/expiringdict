from time import sleep

from mock import Mock, patch
from nose.tools import assert_raises, eq_, ok_

from expiringdict import ExpiringDict


def test_create():
    assert_raises(AssertionError, ExpiringDict, max_len=1, max_age_seconds=-1)
    assert_raises(AssertionError, ExpiringDict, max_len=0, max_age_seconds=1)

    d = ExpiringDict(max_len=3, max_age_seconds=0.01)
    eq_(len(d), 0)


def test_basics():
    d = ExpiringDict(max_len=3, max_age_seconds=0.01)

    eq_(d.get('a'), None)
    d['a'] = 'x'
    eq_(d.get('a'), 'x')

    sleep(0.01)
    eq_(d.get('a'), None)

    d['a'] = 'y'
    eq_(d.get('a'), 'y')

    ok_('b' not in d)
    d['b'] = 'y'
    ok_('b' in d)

    sleep(0.01)
    ok_('b' not in d)

    # a is still in expiringdict, next values should expire it
    d['c'] = 'x'
    d['d'] = 'y'
    d['e'] = 'z'

    # dict if full
    ok_('c' in d)
    ok_('d' in d)

    d['f'] = '1'
    # c should gone after that
    ok_('c' not in d, 'Len of dict is more than max_len')

    # test __delitem__
    del d['e']
    ok_('e' not in d)


def test_pop():
    d = ExpiringDict(max_len=3, max_age_seconds=0.01)
    d['a'] = 'x'
    eq_('x', d.pop('a'))
    sleep(0.01)
    eq_(None, d.pop('a'))


def test_repr():
    d = ExpiringDict(max_len=2, max_age_seconds=0.01)
    d['a'] = 'x'
    eq_(str(d), "ExpiringDict([('a', 'x')])")
    sleep(0.01)
    eq_(str(d), "ExpiringDict([])")


def test_iter():
    d = ExpiringDict(max_len=10, max_age_seconds=0.01)
    eq_([k for k in d], [])
    d['a'] = 'x'
    d['b'] = 'y'
    d['c'] = 'z'
    eq_([k for k in d], ['a', 'b', 'c'])

    eq_([k for k in d.values()], ['x', 'y', 'z'])
    sleep(0.01)
    eq_([k for k in d.values()], [])


def test_clear():
    d = ExpiringDict(max_len=10, max_age_seconds=10)
    d['a'] = 'x'
    eq_(len(d), 1)
    d.clear()
    eq_(len(d), 0)


def test_ttl():
    d = ExpiringDict(max_len=10, max_age_seconds=10)
    d['a'] = 'x'

    # existent non-expired key
    ok_(0 < d.ttl('a') < 10)

    # non-existent key
    eq_(None, d.ttl('b'))

    # expired key
    with patch.object(ExpiringDict, '__getitem__',
                      Mock(return_value=('x', 10**9))):
        eq_(None, d.ttl('a'))


def test_setdefault():
    d = ExpiringDict(max_len=10, max_age_seconds=0.01)

    eq_('x', d.setdefault('a', 'x'))
    eq_('x', d.setdefault('a', 'y'))

    sleep(0.01)

    eq_('y', d.setdefault('a', 'y'))


def test_not_implemented():
    d = ExpiringDict(max_len=10, max_age_seconds=10)
    assert_raises(NotImplementedError, d.fromkeys)
    assert_raises(NotImplementedError, d.viewitems)
    assert_raises(NotImplementedError, d.viewkeys)
    assert_raises(NotImplementedError, d.viewvalues)


def test_cleanup_on_length():
    d = ExpiringDict(max_len=10, max_age_seconds=0.01)
    d['a'] = 'x'
    eq_(1, len(d))
    sleep(0.01)
    eq_(0, len(d))

    d = ExpiringDict(max_len=10, max_age_seconds=0.02)
    d['a'] = 1
    sleep(0.01)
    eq_(1, len(d))
    d['b'] = 2
    sleep(0.01)
    eq_(1, len(d))
    d['c'] = 3
    sleep(0.01)
    eq_(1, len(d))
    d['d'] = 4
    sleep(0.01)
    eq_(1, len(d))

    d = ExpiringDict(max_len=1000, max_age_seconds=.5)
    d[1] = 1
    d[2] = 2
    d[3] = 3
    d[4] = 4

    ok_(1 in d)
    ok_(2 in d)
    ok_(3 in d)
    ok_(4 in d)
    eq_(4, len(d))

    sleep(.25)
    d[1] = 1
    d[2] = 2
    sleep(.40)
    ok_(1 in d)
    ok_(2 in d)
    ok_(3 not in d)
    ok_(4 not in d)
