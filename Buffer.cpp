
// must be first include because of Python stuff, see ffmpeg.h comment
#include "PyThreading.hpp" // mlock

#include <algorithm>
#include "Buffer.hpp"

Buffer::Chunk::Chunk() : start(0), end(0) { mlock(this, sizeof(*this)); }
Buffer::Buffer() : _size(0) { mlock(this, sizeof(*this)); }

size_t Buffer::pop(uint8_t* target, size_t target_size) {
	size_t c = 0;
	while(!chunks.empty()) {
		auto chunkPtr = chunks.front();
		Chunk& chunk = chunkPtr->value;
		int s = chunk.end - chunk.start;
		assert(s > 0);
		if((size_t)s > target_size) s = (int)target_size;
		memcpy(target, chunk.data + chunk.start, s);
		chunk.start += s;
		_size -= s;
		target += s;
		target_size -= s;
		c += s;
		if(chunk.start < chunk.end) {
			assert(target_size == 0);
			break;
		}
		if(chunk.freeDataAvailable()) {
			// push() would have filled it further
			break;
		}
		chunks.pop_front();
	}
	return c;
}

void Buffer::push(const uint8_t* data, size_t size) {
	size_t sizeOrig(size);
	while(size > 0) {
		auto chunkBackPtr = chunks.back();
		if(!chunkBackPtr->isData(true)) // it means chunks is empty
			chunks.push_back();
		else if(!chunkBackPtr->value.freeDataAvailable())
			chunks.push_back();
		auto chunkPtr = chunks.back();
		assert(chunkPtr->isData(false));
		Chunk& chunk = chunkPtr->value;
		size_t s = std::min(size, (size_t)chunk.freeDataAvailable());
		memcpy(chunk.data + chunk.end, data, s);
		data += s;
		size -= s;
		chunk.end += s;
	}
	_size += sizeOrig;
}

