
#include "Buffer.cpp"

#include <thread>

void test1() {
	Buffer buf;

#define N 10000
	auto producer = [&buf](){
		for(uint32_t i = 0; i < N; ++i) {
			buf.push((uint8_t*)&i, sizeof(uint32_t));
		}
	};

	auto consumer = [&buf](){
		for(uint32_t i = 0; i < N; ++i) {
			int ret;
			while(buf.size() < sizeof(uint32_t)); // wait for entry
			size_t c = buf.pop((uint8_t*)&ret, sizeof(uint32_t));
			assert(c == sizeof(uint32_t));
			assert(ret == i);
		}
	};

	for(int i = 0; i < 3; ++i) {
		producer();
		assert(buf.size() == N * sizeof(int));
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
