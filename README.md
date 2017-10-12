blackrocktickets
================

How To Administer a Black Rock Tickets project:

You must be a registered user at the site with admin privileges.
Login at https://[site]/admin/

The system is built on dependencies (Parent/Child relationships), so before the desired ticket tier or volunteer shift can be created, it’s parents (and grandparents) must be created, starting with the top generation. Once the parent is created, then children can be added, then those children can have children below them.

For Event Ticketing:
The hierarchy for the ticketing section is: Site > Event > Occurrence > Tier
So before an Occurrence can be created (like AB2017), an Event must be created.

Site: the website for ticketing
Domain name: (url)
Display name: (name of event)

Event: the recurring event we host
Site: parent (site object)
Header: name or url of logo that is displayed to user next to Occurrence description
Label: the title shown to the user
Description: shown to user to describe the event; use html for formatting and links
Admin email: the email shown to user for more info
Survival guide: link to that document
Waiver: link to the Event Waiver document
Receipt text: shown to user after purchase; use html for formatting and links
Paypal user: _
Paypal password: _
Paypal signature: _
Paypay currency: _
Admin: select the users which are allowed to make changes to this listing.

Occurrence: the specific event with dates and times
Event: parent
Label: the specific name/theme of this event (AB2017: Restoration)
Code: _
Start date: when the event officially starts
End date: when the event officially ends
Cap: total number of tickets available
Description: shown to user about this specific event; use html for formatting and links
Allow donations: allows user to add a donation to their purchase from the available Options
    Options: highlight the additional options or donations available to select for purchase; click the plus sign to add more
    Coupons: allowed coupon codes for this event; click the plus sign to add more

Tier: the ticket releases for the Occurrence
Occurrence: parent
Label: name of the Tier (First Chance General Sale)
Description: shown to user any info about of this tier, including its limits, breakdown of costs, instructions, etc; use html for formatting
Code: _
Start date: the exact date and time this tier becomes available and the system allows purchases
End date: the exact date and time this tier becomes unavailable and the system discontinues purchases
Price: amount; do not include dollar sign
Cap: number of tickets available in this Tier before considered Sold Out
Password: optional password required to purchase tickets within this Tier. If a password is set, the Tier is hidden so not found accidentally. To access it, add "?show=show" to the end of the buy url.
Use queue: _
Max purchase: maximum tickets allowed to be purchased in a single transaction; once complete, users can still make more transactions for additional tickets
Reservation required: _
Is lottery: _
Require code: _

Options: additional options or donations available for purchase when buying a ticket
Label: name of the Option shown to user
Description: shown to user any info about of this Option, including its limits, special instructions, etc; use html for formatting
Price: amount; do not include dollar sign

Coupons: available coupon codes for discount on purchases
    Label: the name of this coupon
    Key: the coupon code
    Discount: discounted cost of entire purchase (not per ticket)
    Cap: maximum coupons available

Chances: _
User: _
Tier: _
Name: _
Email: _
Request date: _
Queue code: _

Comps: _

Payments: previous payments by users

Purchase requests: previous purchase requests by users

Purchases: previous purchases by users

Tickets: previous tickets purchased by users

User profiles: 

Queued tiers:
Name: _
Url: _
Starts: _
Ends: _
Max active: _
Max tickets: _
Cap: _
Average tickets: _
Ticket count ready: _
Ticket count started: _
Ticket count finished: _
Ticket count paid: _

Reservations: _



For Scheduling: 
The hierarchy for the Volunteer Scheduling section is: Event > Schedule > Position
So the Schedule must be created (like Rangers) before a Position can be created (like Alpha Ranger). Event: the event we host; created above under Ticketing. Once Schedules are created, they must be attached to the upcoming Event Occurrence, by adding a Signups window (when volunteering shifts can be reserved). Read below for further explanations of each topic.

Schedule: the grouping category for similar Positions, often times from the same team/department.
Event: parent
Label: name of this Schedule shown to user 
Block size: time duration in minutes of the blocks in the schedule matrix, usually the length of a single shift (or smaller if there’s multiple staggered shifts on the same schedule)
Start offset: time in minutes from the beginning of the Occurrence which this Schedule starts (can be negative in case a shift starts before the official start time of the Occurrence)
End offset: time in minutes from the end of the Occurrence which this Schedule ends (use negative minutes to end early)
Reminder email:  _
Description: description of Schedule show to user
Admins: select the users which are allowed to make changes to this listing.
Notes: The important thing here is the block size. It's in minutes, and is usually the length of a single shift, but it might be smaller if you have multiple staggered shifts on a schedule. So maybe you have greeters and parking on two hour shifts on the same schedule, but the greeters rotate on even hours and parking on odd hours, in which case you'd set a block size of 60 so the schedule is broken up properly. The offsets allow you to start and end the schedule before or after the event start and end dates (for example you'd want greeter shifts to begin before gates open).

Position: the specific position/job/task that needs volunteers. It has a specific job description, shift length, max users, etc. (from the developer: “You can also set up hierarchies here, which will allow you to create shift lengths or max users that change This is a bit tricky to get right.”)
Schedule: parent
Label: name of the Position that the user is signing up for
Shift offset: [number of Blocks to offset, up to max shift length?; need to research more] _
Shift length: how many time Blocks compose a shift
Max users: number of users who can fill the shift before it’s considered full.
Detail required:  _
Parent: _
Description: description of Position show to user
Sort: integer compared to other Position’s Sort integer to determine their displayed order
Notes: It's tied to a shift, and its offset and length are relative to the block size of its schedule (so in the example above, the shift length would be 2 for 2 hours (since the schedule block size is 60 minutes). You can also set up hierarchies here, which will allow you to create shift lengths or max users that change This is a bit tricky to get right.

Blackouts: groups of Blocks when a Position does not need any Shifts filled.
Position: parent
Label: name of this Blackout shown to user in the portion of the Schedule that is unavailable
Start block: number of Blocks from the beginning of the Schedule to start this Blackout
End block: number of Blocks from the beginning of the Schedule to end this Blackout

Shifts: all shifts that users have signed up for.


Sign ups: the sign up window during which users are allowed to visit the website and sign up for shifts for the selected Occurrence. By creating a new Signup record for each Event Occurrence, the rest of the setup data usually stays the same so can be reused or slightly edited.
Occurrence: parent
Start date: when the window opens to start allowing users to sign up for shifts
End date: when the signup window closes and shifts can no longer be edited
Schedules: all schedules which can be browsed and signed up for by users (if more schedules are added later, make sure to also add them here)
Admins: select the users which are allowed to make changes to this listing.





