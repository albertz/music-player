
// must be first include because of Python stuff, see ffmpeg.h comment
#include "PyThreading.hpp" // mlock

#include <algorithm>
#include "Buffer.hpp"

Buffer::Chunk::Chunk() : start(0), end(0) { mlock(this, sizeof(*this)); }
Buffer::Buffer() : _size(0) { mlock(this, sizeof(*this)); }

size_t Buffer::pop(uint8_t* target, size_t target_size, bool doCleanup) {
	size_t c = 0;
	for(Chunk& chunk : chunks) {
		Chunk::Idx chunkEnd = chunk.end;
		if(chunk.start == 0 && chunkEnd == 0) {
			// push() but not yet any data added
			break;
		}
		int s = chunkEnd - chunk.start;
		if(s == 0) continue;
		if((size_t)s > target_size) s = (int)target_size;
		memcpy(target, chunk.data + chunk.start, s);
		chunk.start += s;
		_size -= s;
		target += s;
		target_size -= s;
		c += s;
		if(chunk.start < chunkEnd) {
			assert(target_size == 0);
			break;
		}
		if(chunkEnd < Chunk::BufferSize()) {
			// push() would have filled it further
			break;
		}
		assert(chunk.start == chunkEnd);
		assert(chunkEnd == Chunk::BufferSize());

		// This can be heavy (the `free`ing), so we might want to do it elsewhere.
		if(doCleanup)
			chunks.pop_front();
	}
	return c;
}

void Buffer::push(const uint8_t* data, size_t size) {
	while(size > 0) {
		auto chunkBackPtr = chunks.back();
		if(!chunkBackPtr) // it means chunks is empty
			chunks.push_back();
		else if(!chunkBackPtr->value.freeDataAvailable())
			chunks.push_back();
		auto chunkPtr = chunks.back();
		assert(chunkPtr && chunkPtr->isData(false));
		Chunk& chunk = chunkPtr->value;
		size_t s = std::min(size, (size_t)chunk.freeDataAvailable());
		assert(s > 0);
		memcpy(chunk.data + chunk.end, data, s);
		data += s;
		size -= s;
		chunk.end += s;
		_size += s;
	}
}

void Buffer::cleanup() {
	while(!chunks.empty()) {
		auto chunkPtr = chunks.front();
		Chunk& chunk = chunkPtr->value;
		if(chunk.end < Chunk::BufferSize()) break;
		if(chunk.size() > 0) break;
		chunks.pop_front();
	}
}
