
#include "Buffer.cpp"

#include <thread>

void test1() {
	Buffer buf;

	auto producer = [&buf](){
		for(int i = 0; i < 100; ++i) {
			buf.push((uint8_t*)&i, sizeof(i));
		}
	};

	auto consumer = [&buf](){
		for(int i = 0; i < 100; ++i) {
			int ret;
			while(buf.size() < sizeof(ret)); // wait for entry
			size_t c = buf.pop((uint8_t*)&ret, sizeof(ret));
			assert(c == sizeof(ret));
			assert(ret == i);
		}
	};

	for(int i = 0; i < 1000; ++i) {
		producer();
		assert(buf.size() == 100 * sizeof(int));
		consumer();
		assert(buf.empty());
	}

	for(int i = 0; i < 1000; ++i) {
		std::thread t1(producer), t2(consumer);
		t1.join();
		t2.join();
		assert(buf.empty());
	}
}

int main() {
	test1();
}
