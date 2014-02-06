//
//  TableViewDelegate.m
//  MusicPlayer
//
//  Created by Albert Zeyer on 07.11.13.
//  This code is under the 2-clause BSD license, see License.txt in the root directory of this project.
//

#import "TableViewDelegate.h"


@implementation _TableViewDelegate

@synthesize onSelectionChange;

- (void)tableViewSelectionDidChange:(NSNotification *)notif
{
	if(!onSelectionChange) return;
	
	NSTableView* tableView = [notif object];
	NSArray* selection = [[NSArray alloc] init];
	[[tableView selectedRowIndexes] enumerateIndexesUsingBlock:^(NSUInteger idx, BOOL *stop) {
		// tableView.dataSource().data[index]
		
	}];
	
	
	//onSelectionChange();
	
}

@end
