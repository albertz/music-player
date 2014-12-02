
#include "QtUtils.hpp"
#include "QtApp.hpp"

void dispatch_async_background_queue(boost::function<void()> f) {
	// XXX: other thread, not the main thread
	execInMainThread_async(f);
}

void dispatch_sync_main_queue(boost::function<void()> f) {
	execInMainThread_sync(f);
}


