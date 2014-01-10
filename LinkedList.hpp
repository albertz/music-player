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
		S_PoppedOut,
	};

	struct Item : public boost::intrusive_ref_counter< Item, boost::thread_safe_counter > {
		ItemPtr prev, next;
		ItemPtr prevBackup, nextBackup;
		boost::atomic<ItemState> state;
		T value;

		Item() : state(S_Uninitialized), value() {}

		void reset() {
			state = S_Uninitialized;
			prev = NULL; next = NULL;
			prevBackup = NULL; nextBackup = NULL;
		}

		bool isEmpty() {
			ItemPtr nextCpy(next);
			if(!nextCpy) // can happen when clear() meanwhile
				return true;
			return nextCpy->state != S_Data;
		}

		bool isData(bool alsoPoppedOut = true) {
			if(state == S_Data) return true;
			if(alsoPoppedOut && state == S_PoppedOut) return true;
			return false;
		}

		bool insertBefore(Item* item) {
			item->reset();

			ItemPtr oldPrev = prev.exchange(item);
			item->next = this;

			while(true) {
				if(!oldPrev) {
					// oldPrev == NULL -> clear() or pop_front() item.
					item->next = NULL;
					return false;
				}

				Item* oldPrevNext;
				bool success = oldPrev->next.compare_exchange(this, item, &oldPrevNext);
				// If pop_front() meanwhile and oldPrev was the first item,
				// we might have reset oldPrev->next already or will soon.
				// In the latter case, it will set item->prev = main, ok.
				// If pop_front() meanwhile, we might also have oldPrev==main.
				if((success && oldPrev->state != S_PoppedOut) || (item == oldPrevNext)) {
					item->prev = oldPrev;
					break;
				}
				else if(!success && oldPrev->state == S_MainLink) {
					assert(oldPrev.get() == this);
					// and try again, wait for main->next == this
				}
				else { // !success (-> popped out) or success && popped out
					assert(oldPrev->state == S_PoppedOut);
					if(!success) assert(oldPrevNext == NULL); // pop_front() does this
					oldPrev = oldPrev->prevBackup;
					// and try again
				}
			}

			item->state = S_Data;
			return true;
		}
		
		// WARNING: Not well tested. Also not safe with any other write-operation..
		bool insertAfter(Item* item) {
			ItemPtr nextBackup = next;
			if(!nextBackup) return false;
			assert(nextBackup->prev.get() == this);
			bool res = nextBackup->insertBefore(item);
			if(!res) return false;
			assert(this->next.get() == item);
			assert(item->prev.get() == this);
			assert(item->next == nextBackup);
			assert(nextBackup->prev.get() == item);
			return true;
		}
		
		void popOut(ItemPtr expectedPrev = NULL) {
			prevBackup = prev;
			nextBackup = next;
			state = S_PoppedOut;
		
			if(!expectedPrev)
				expectedPrev = getPrev();
			
			ItemPtr firstNext = next.exchange(NULL);
			if(firstNext) { // can happen to be NULL when clear() meanwhile
				// e.g. if firstNext==main and push_front() meanwhile,
				// main->prev != first. in that case, don't change.
				firstNext->prev.compare_exchange(this, expectedPrev);
				
				if(!expectedPrev->next.compare_exchange(this, firstNext))
					assert(false); // this can only happen if there was another consumer
			}
			
			prev = NULL;
		}
		
		ItemPtr getNext() const {
			ItemPtr newPtr = next;
			if(!newPtr || state == S_PoppedOut)
				newPtr = nextBackup;
			return newPtr;
		}
		
		ItemPtr getPrev() const {
			ItemPtr newPtr = prev;
			if(!newPtr || state == S_PoppedOut)
				newPtr = prevBackup;
			return newPtr;
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
			ItemPtr nextPtr = ptr->next.exchange(NULL);
			if(!nextPtr) nextPtr = ptr->nextBackup;
			ptr->prevBackup = NULL;
			ptr->nextBackup = NULL;
			ptr = nextPtr;
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

	// The iterator itself is not thread-safe, i.e. you can't access
	// a single iterator from multiple threads. However,
	// the list can be accessed and modified from other threads.
	struct Iterator {
		ItemPtr ptr;

		Iterator(const ItemPtr& _ptr) : ptr(_ptr) {}

		T& operator*() {
			return ptr->value;
		}

		Iterator& operator++() {
			if(!isEnd())
				ptr = ptr->getNext();
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
			if(!ptr->isData(true)) return true;
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
		bool success = mainCpy->insertBefore(item);
		assert(success);
		return item;
	}

	// WARNING: Not properly tested!
	// WARNING: pop_front() must not be used meanwhile. (Can be fixed easily though.)
	// WARNING: Probably also other functions must not be called.
	// However, reading from this list is save meanwhile.
	ItemPtr push_front(ItemPtr item = NULL) {
		ItemPtr mainCpy(main);
		if(!item) item.reset(new Item());
		bool success = mainCpy->insertAfter(item);
		assert(success);
		return item;
	}

	// only single consumer supported.
	// parallel reading is supported though
	ItemPtr pop_front() {
		ItemPtr mainCpy(main);
		ItemPtr first = mainCpy->next;
		if(!first || first == mainCpy || first->state != S_Data)
			return NULL;
		first->popOut(mainCpy);
		return first;
	}

	// WARNING: Not properly tested!
	// No other writing op must be used meanwhile!
	// Meanwhile-reading should be safe.
	ItemPtr pop_back() {
		ItemPtr mainCpy(main);
		ItemPtr last = mainCpy->prev;
		if(!last || last == mainCpy || last->state != S_Data)
			return NULL;
		last->popOut();
		return last;
	}

	void clear() {
		ItemPtr oldMain = main.exchange(_newMain());
		_releaseMain(oldMain);
	}

	bool empty() {
		return ItemPtr(main)->isEmpty();
	}

	ItemPtr front() const {
		ItemPtr ptr = ItemPtr(main)->next;
		if(ptr.get() && ptr->isData(false)) return ptr;
		return NULL;
	}
	ItemPtr back() const {
		ItemPtr ptr = ItemPtr(main)->prev;
		if(ptr.get() && ptr->isData(false)) return ptr;
		return NULL;
	}

	// Be careful with this element.
	ItemPtr mainLink() const { return main; }


	// not threading-safe!
	// we don't keep a seperate size-counter by intention to simplify things for now.
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
