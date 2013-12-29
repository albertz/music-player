#ifndef MP_LINKEDLIST_HPP
#define MP_LINKEDLIST_HPP

#include <boost/smart_ptr/intrusive_ref_counter.hpp>
#include <boost/atomic.hpp>
#include <assert.h>
#include "IntrusivePtr.hpp"

// lockfree

template<typename T>
class LinkedList {
public:
	struct Item;
	typedef IntrusivePtr<Item> ItemPtr;

	enum ItemState {
		S_Uninitialized,
		S_MainLink,
		S_Data,
	};

	struct Item : public boost::intrusive_ref_counter< Item, boost::thread_safe_counter > {
		ItemPtr prev, next;
		boost::atomic<ItemState> state;
		T value;

		Item() : state(S_Uninitialized), value() {}

		bool isEmpty() {
			ItemPtr nextCpy(next);
			if(!nextCpy) // can happen when clear() meanwhile
				return true;
			return nextCpy->state != S_Data;
		}

		bool insertBefore(ItemPtr& item) {
			ItemPtr oldPrev = prev.exchange(item);
			if(oldPrev) {
				ItemPtr oldPrevNext = oldPrev->next.exchange(item);
				// If pop_front() meanwhile and oldPrev was the first item,
				// we might have reset oldPrev->next already or will soon.
				// In the latter case, it will set item->prev = main, which is correct;
				// we do the same here, it doesn't matter which comes first.
				// Otherwise, we get here:
				if(!oldPrevNext) {
					// oldPrev is being returned by pop_front()
					oldPrev->next = NULL;
				}
				else {
					item->prev = oldPrev;
				}
			} else {
				// oldPrev == NULL -> clear() or pop_front() item.
				return false;
			}
			item->next = this;
			return true;
		}
	};

private:
	ItemPtr main; // prev = last, next = first

	ItemPtr _newMain() {
		ItemPtr m = new Item();
		m->next = m;
		m->prev = m;
		m->state = S_MainLink;
		return m;
	}

	void _releaseMain(const ItemPtr& m) {
		ItemPtr ptr = m;
		while(true) {
			ptr = ptr->next.exchange(NULL);
			if(!ptr) break;
		}
		ptr = m;
		while(true) {
			ptr = ptr->prev.exchange(NULL);
			if(!ptr) break;
		}
	}

public:
	LinkedList() {
		main = _newMain();
	}

	~LinkedList() {
		clear();

	}

	// The iterator is not thread-safe, i.e. you can't access
	// a single iterator from multiple threads. However,
	// the list can be accessed and modified from other threads.
	struct Iterator {
		ItemPtr ptr;

		Iterator(const ItemPtr& _ptr) : ptr(_ptr) {}

		T& operator*() {
			return ptr->value;
		}

		Iterator& operator++() {
			if(isEnd()) return *this;
			ptr = ptr->next;
			return *this;
		}

		bool operator==(const Iterator& other) const {
			if(isEnd() && other.isEnd()) return true;
			return ptr == other.ptr;
		}

		bool operator!=(const Iterator& other) const {
			return !(*this == other);
		}

		bool isEnd() const {
			if(ptr.get() == NULL) return true;
			if(ptr->state != S_Data) return true;
			return false;
		}
	};

	Iterator begin() {
		ItemPtr backup(main);
		return Iterator(backup->next);
	}

	Iterator end() {
		return Iterator(NULL);
	}

	// only single producer supported
	ItemPtr push_back(ItemPtr item = NULL) {
		ItemPtr mainCpy(main);
		if(!item) item.reset(new Item());
		item->state = S_Uninitialized;
		mainCpy->insertBefore(item);
		item->state = S_Data;
		return item;
	}

	// only single consumer supported
	ItemPtr pop_front() {
		ItemPtr mainCpy(main);
		ItemPtr first = mainCpy->next;
		if(!first || first == mainCpy || first->state != S_Data)
			return NULL;
		first->prev = NULL;
		ItemPtr firstNext = first->next.exchange(NULL);
		if(firstNext) // can happen to be NULL when clear() meanwhile
			firstNext->prev = mainCpy;
		mainCpy->next = firstNext;
		return first;
	}

	void clear() {
		ItemPtr oldMain = main.exchange(_newMain());
		_releaseMain(oldMain);
	}

	bool empty() {
		return ItemPtr(main)->isEmpty();
	}

	// be very careful! noone must use pop_front() or clear() meanwhile
	T& front() { return main->next->value; }
	T& back() { return main->prev->value; }


	// not threading-safe!
	size_t size() {
		ItemPtr ptr = main;
		size_t c = 0;
		while(true) {
			ptr = ptr->next;
			if(ptr->state != S_Data) break;
			c++;
		}
		return c;
	}

	// not threading-safe!
	void _checkSanity() {
		assert(main->state == S_MainLink);
		ItemPtr ptr = main;
		size_t c1 = 0;
		while(true) {
			assert(ptr->next->prev == ptr);
			assert(ptr->prev->next == ptr);
			ptr = ptr->next;
			if(ptr->state == S_MainLink) break;
			else if(ptr->state == S_Data) {} // ok
			else if(ptr->state == S_Uninitialized) assert(false);
			else assert(false);
			c1++;
		}
		assert(ptr->state == S_MainLink);
		size_t c2 = 0;
		ptr = main;
		while(true) {
			assert(ptr->next->prev == ptr);
			assert(ptr->prev->next == ptr);
			ptr = ptr->prev;
			if(ptr->state == S_MainLink) break;
			else if(ptr->state == S_Data) {} // ok
			else if(ptr->state == S_Uninitialized) assert(false);
			else assert(false);
			c2++;
		}
		assert(ptr->state == S_MainLink);
		assert(c1 == c2);
		if(c1 == 0) {
			assert(main->next == main);
			assert(main->prev == main);
		}
	}
};


#endif // LINKEDLIST_HPP
