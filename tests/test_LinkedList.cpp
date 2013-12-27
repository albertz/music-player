
#include <assert.h>
#include <thread>
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


void test2() {
	LinkedList<int> l;
	l._check_sanity();

	auto producer = [&l](){
		for(int i = 0; i < 100; ++i) {
			LinkedList<int>::ItemPtr item(new LinkedList<int>::Item);
			item->value = i;
			l.push_back(item);
		}
	};

	auto consumer = [&l](){
		for(int i = 0; i < 100; ++i) {
			while(l.empty()); // wait for entry
			auto ret = l.pop_front();
			assert(ret);
			assert(ret->value == i);
		}
	};

	for(int i = 0; i < 1000; ++i) {
		std::thread t1(producer), t2(consumer);
		t1.join();
		t2.join();
		assert(l.empty());
		l._check_sanity();
	}
}


int main() {
	test1();
	test2();
}
