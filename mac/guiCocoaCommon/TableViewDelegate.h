//
//  TableViewDelegate.h
//  MusicPlayer
//
//  Created by Albert Zeyer on 07.11.13.
//  This code is under the 2-clause BSD license, see License.txt in the root directory of this project.
//

#import <Foundation/Foundation.h>
#import <AppKit/NSTableView.h>

typedef void (^OnSelectionChange)(NSArray*);

@interface _TableViewDelegate : NSObject<NSTableViewDelegate>

@property OnSelectionChange onSelectionChange;

- (void)tableViewSelectionDidChange:(NSNotification *)notification;

@end
