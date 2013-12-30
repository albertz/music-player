
#include "Buffer.cpp"

#include <thread>

void test1() {
	Buffer buf;

#define N 10000
	// We want to force multiple buffer chunks.
	assert(N * sizeof(uint32_t) > BUFFER_CHUNK_SIZE);

	auto producer_ = [&buf](int start, int end){
		for(uint32_t i = start; i < end; ++i) {
			buf.push((uint8_t*)&i, sizeof(uint32_t));
		}
	};
	auto producer = [&]() { producer_(0, N); };

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

	for(int i = 0; i < 30; ++i) {
		std::thread t1(producer), t2(consumer);
		t1.join();
		t2.join();
		assert(buf.empty());
	}

	for(int i = 0; i < 10; ++i) {
		producer_(0, N/2);
		std::thread t1([&](){ producer_(N/2, N); }), t2(consumer);
		t1.join();
		t2.join();
		assert(buf.empty());
	}
}

int main() {
	test1();
}
