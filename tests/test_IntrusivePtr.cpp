
#include <boost/smart_ptr/intrusive_ref_counter.hpp>
#include "IntrusivePtr.hpp"

struct Item;
typedef IntrusivePtr<Item> ItemPtr;

struct Item : public boost::intrusive_ref_counter< Item, boost::thread_safe_counter > {
	ItemPtr next;
	int value;

	Item(int v = 0) : value(v) {}
};


int main() {
	IntrusivePtr<Item> p1(new Item(12));
	IntrusivePtr<Item> p2(new Item(23));
	IntrusivePtr<Item> p3(new Item(34));

	p2 = p1;
	p2 = NULL;
	p2 = p1;

	p2->next = p3;

	for(int i = 0; i < 100; ++i) {
		ItemPtr _tmp = p2;

		p2 = NULL;
		p1 = p2;
	}

}
