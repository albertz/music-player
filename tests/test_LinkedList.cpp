
#include <assert.h>
#include <thread>
#include <boost/atomic.hpp>

#include "LinkedList.hpp"

void test0() {
	LinkedList<int> l;
	assert(l.empty());
	l._checkSanity();

	auto item = l.push_back();
	item->value = 42;
	item = NULL;
	l._checkSanity();
	assert(!l.empty());
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

	assert(!l.empty());
	assert(l.size() == 100);

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
			while(l.empty()) {} // wait for entry
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


void test3() {
	LinkedList<int> l;
	boost::atomic<int> state;

	auto producer = [&l, &state](){
		for(int i = 0; i < 100; ++i) {
			if(i == 50) state++;
			LinkedList<int>::ItemPtr item(new LinkedList<int>::Item);
			item->value = i;
			l.push_back(item);
		}
		state++;
	};

	auto consumer = [&l, &state](){
		while(state == 0) {}
		for(int i = 0; i < 40; ++i) {
			while(l.empty()); // wait for entry
			auto ret = l.pop_front();
			assert(ret);
			assert(ret->value == i);
		}
		state++;
	};

	auto reader = [&l, &state]() {
		while(state < 3) {
			if(state == 0) continue;
			int first = -1;
			int old = -1;
			int count = 0;
			for(auto v : l) {
				assert(v >= 0);
				if(first < 0) first = v;
				if(old >= 0) assert(old < v);
				old = v;
				++count;
			}
			assert(count > 10);
		}
	};

	for(int i = 0; i < 1000; ++i) {
		state = 0;

		std::thread t1(producer), t2(consumer), t3(reader);
		t1.join();
		t2.join();
		t3.join();

		l._checkSanity();
		l.clear();
	}
}

void test4() {
	LinkedList<int> l;

	auto producer = [&l](){
		for(int i = 3; i <= 150; ++i) {
			LinkedList<int>::ItemPtr item(new LinkedList<int>::Item);
			item->value = i;
			if(i < 50)
				l.push_back(item);
			else
				l.push_front(item);
		}

		for(int i = 150; i > 100; --i) {
			LinkedList<int>::ItemPtr item = l.pop_front();
			assert(item->value == i);
		}
	};

	auto reader = [&l]() {
		int endCount = 0;
		while(true) {
			int old = -1;
			int m = 0;
			int count = 0;
			for(auto v : l) {
				assert(v >= 1);
				if(old >= 50 && v == 1) {}
				else if(old >= 50) assert(old - 1 == v);
				else if(old >= 0) assert(old + 1 == v);
				old = v;
				if(v > m) m = v;
				++count;
				assert(count <= 150);
			}
			assert(count >= 2);
			assert(count == m);
			if(count >= 50) assert(old == 49);
			if(count < 100) assert(endCount == 0);
			if(count == 100) endCount++;
			if(endCount >= 10) break;
		}
	};

	for(int i = 0; i < 1000; ++i) {
		l.push_back()->value = 1;
		l.push_back()->value = 2;

		std::thread t1(producer), t3(reader);
		t1.join();
		t3.join();

		l._checkSanity();
		l.clear();
	}
}

int main() {
	test0();
	test1();
	test2();
	test3();
	test4();
}
