
#include <assert.h>
#include "LinkedList.hpp"

void test1() {
	LinkedList<int> l;
	l._check_sanity();

	for(int i = 0; i < 100; ++i) {
		auto item = l.push_back();
		l._check_sanity();
		item->value = i;
	}

	for(int i = 0; i < 100; ++i) {
		auto ret = l.pop_front();
		l._check_sanity();
		assert(ret);
		assert(ret->value == i);
	}

	assert(l.empty());
}

int main() {
	test1();
}
