
#include <assert.h>
#include <thread>

#include "LinkedList.hpp"

void test0() {
	LinkedList<int> l;
	l._checkSanity();

	auto item = l.push_back();
	item->value = 42;
	item = NULL;
	l._checkSanity();
	assert(l.size() == 1);

	auto ret = l.pop_front();
	assert(ret);
	assert(ret->value == 42);
	ret = NULL;

	assert(l.empty());
	assert(l.size() == 0);
	l._checkSanity();
}


void test1() {
	LinkedList<int> l;
	l._checkSanity();

	for(int i = 0; i < 100; ++i) {
		auto item = l.push_back();
		l._checkSanity();
		item->value = i;
	}

	for(int i = 0; i < 100; ++i) {
		auto ret = l.pop_front();
		l._checkSanity();
		assert(ret);
		assert(ret->value == i);
	}

	assert(l.empty());
}


void test2() {
	LinkedList<int> l;
	l._checkSanity();

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
		l._checkSanity();
	}
}


int main() {
	test0();
	test1();
	test2();
}
