//
//  AppDelegate.m
//  MusicPlayer
//
//  Created by Albert Zeyer on 17.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import "AppDelegate.h"

@implementation AppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)aNotification
{
	printf("My app delegate: finish launching\n");
}

-(void)dealloc
{
	printf("My app delegate dealloc\n");
}

@end
