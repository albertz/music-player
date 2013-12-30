#ifndef MP_BUFFER_HPP
#define MP_BUFFER_HPP

#include <boost/atomic.hpp>
#include <stdint.h>
#include "LinkedList.hpp"

#define BUFFER_CHUNK_SIZE (1024 * 4)

struct Buffer {

	struct Chunk {
		uint8_t data[BUFFER_CHUNK_SIZE];
		boost::atomic<uint16_t> start, end;
		uint8_t* pt() { return data + start; }
		uint16_t size() const { assert(start <= end); return end - start; }
		static uint16_t BufferSize() { return BUFFER_CHUNK_SIZE; }
		uint16_t freeDataAvailable() { return BufferSize() - end; }
		Chunk();
	};
	LinkedList<Chunk> chunks;
	boost::atomic<size_t> _size;

	Buffer();
	
	// these are all not multithreading safe
	size_t size() { return _size; }
	void clear() { _size = 0; chunks.clear(); }
	bool empty() { return size() == 0; }

	// returns amount of data returned, i.e. <= target_size
	// single consumer supported
	size_t pop(uint8_t* target, size_t target_size);

	// single producer supported
	void push(const uint8_t* data, size_t size);
};

#endif // BUFFER_HPP
