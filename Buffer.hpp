#ifndef MP_BUFFER_HPP
#define MP_BUFFER_HPP

#include <list>
#include "PyThreading.hpp"

#define BUFFER_CHUNK_SIZE (1024 * 4)

struct Buffer {
	PyMutex mutex;

	struct Chunk {
		uint8_t data[BUFFER_CHUNK_SIZE];
		uint16_t start, end;
		uint8_t* pt() { return data + start; }
		uint16_t size() const { assert(start <= end); return end - start; }
		static uint16_t BufferSize() { return BUFFER_CHUNK_SIZE; }
		uint16_t freeDataAvailable() { return BufferSize() - end; }
		Chunk() : start(0), end(0) { mlock(this, sizeof(*this)); }
	};
	std::list<Chunk> chunks;
	size_t _size;

	Buffer() : _size(0) { mlock(this, sizeof(*this)); }
	size_t size() { PyScopedLock lock(mutex); return _size; }
	void clear() { PyScopedLock lock(mutex); chunks.clear(); _size = 0; }
	bool empty() { return size() == 0; }

	// returns amount of data returned, i.e. <= target_size
	size_t pop(uint8_t* target, size_t target_size);

	void push(const uint8_t* data, size_t size);
};

#endif // BUFFER_HPP
