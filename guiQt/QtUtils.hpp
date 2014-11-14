#ifndef __MP_QTUTILS_HPP
#define __MP_QTUTILS_HPP

#include <boost/function.hpp>

inline void dispatch_async_background_queue(boost::function<void()>) {}
inline void dispatch_sync_main_queue(boost::function<void()>) {}

#endif // QTUTILS_HPP
