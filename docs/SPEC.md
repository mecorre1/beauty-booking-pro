# SPEC.md - Beauty Booking App

## Overview
A web app for a hairdressing salon. Clients book appointments online.
The hairdresser manages her calendar and bookings via a back office.

## Users
- **Client**: books, edits, or cancels appointments
- **Hairdresser (admin)**: manages calendar, views/edits bookings, contacts clients
- Multi-admin is out of scope for MVP

---

## Client-facing flow

### 1. Landing page
- Marketing content (out of scope for MVP)
- Entry point to the booking flow

### 2. Service selection
- Client selects gender first (Male / Female) - impacts service duration
- Client selects service type via clickable cards (not dropdowns):
  - Regular haircut
  - Haircut + hairdressing
  - Color
- Client selects location: At the salon / At home
  - At-home adds an extra charge and internal travel buffer (not shown to client)

### 3. Slot selection
- Weekly calendar view of available slots, filtered by selected service duration
- Client can navigate forward and backward by week
- Weeks run Monday to Sunday
- Slots grouped by time of day:
  - Morning: 00:00 - 11:59
  - Afternoon: 12:00 - 16:59
  - Evening: 17:00 - 23:59
- Empty groups are hidden
- Available slots derived from: weekly schedule minus exceptions minus existing bookings

### 4. Confirmation
- Displays: service type, gender, location, duration, price
- Client fills in: name, email, phone
- Checkbox: agreement to terms and conditions (required) - placeholder content for MVP
- Checkbox: opt-in to marketing communications (optional) - stored on client record
- Confirmation email sent on booking
- Client receives a link to edit or cancel their booking (no deadline)
- Service description shown post-confirmation only (to maximize conversion)

### 5. Editing a booking
- Client can change everything (service, slot, location, contact info)
- During editing, the client's current slot is treated as available
- The rest of the flow is identical to a new booking

---

## Pricing

- Admin can define prices per datetime range (e.g. weekends, summer)
- Price at time of booking is stored as a snapshot on the booking record
- Rule-based pricing engine is out of scope for MVP

---

## Salon

- Salon is an entity with its own data (name, address, contact info)
- Salon address at time of booking is stored as a snapshot on the booking record

---

## Schedule & slots

### Weekly templates
- Admin can create multiple weekly schedule templates
- Each template defines slots across a week (day, start time, duration)
- A template can be applied to a specific calendar week
- Applying a template generates slots for that week (snapshot - changes to the template do not affect already-applied weeks)
- Individual slots within an applied week can be manually edited or deleted

### Slots
- Each slot has: date, start time, end time, is_available
- One booking per slot (no double booking)
- At-home bookings occupy additional internal buffer time after the slot end time

---

## Back office

- Email/password authentication
- Dashboard: list of all upcoming and past bookings
- Calendar view of scheduled slots and bookings
- Per booking: view details, edit, cancel, see client contact info
- Manage weekly templates (create, edit, apply to a week)
- Manage salon entity (name, address, etc.)
- Manage service pricing (set price per datetime range)

---

## Data model

### Salon
- name, address, phone, email
- (address snapshotted on each booking)

### Service
- type: enum (haircut | haircut_hairdressing | color)
- gender: enum (male | female)
- base_duration_minutes
- at_home_buffer_minutes (internal only)

### PriceEntry
- service_id
- valid_from (datetime)
- valid_to (datetime, nullable)
- price

### WeeklyTemplate
- name
- slots: list of TemplateSlot

### TemplateSlot
- day_of_week (0-6)
- start_time
- duration_minutes

### Slot
- date, start_time, end_time
- is_available
- source_template_id (nullable, for reference only)

### Client
- id
- email (unique, primary identifier)
- name
- phone
- marketing_opt_in (bool, default false)
- created_at
- (future: login/auth out of scope for MVP)

### WeeklySchedule
- day_of_week (0-6)
- open_time
- close_time

### AvailabilityException
- id
- start (datetime)
- end (datetime)
- created_at
- comment (nullable, free text)

### BookingMedia
- id (used as filename in storage, e.g. `{media_folder}/{id}`)
- media_type: enum (current_hairstyle | inspiration)
- file_name (original filename for display)
- created_at

### Booking
- id
- slot_id
- service_id
- client_id (FK to Client)
- price_at_booking (snapshot)
- salon_address_at_booking (snapshot)
- location: enum (salon | home)
- home_address (nullable)
- status: enum (confirmed | edited | cancelled)
- edit_token (unique link for client self-service)
- current_hairstyle_media_id (nullable, FK to BookingMedia)
- inspiration_media_id (nullable, FK to BookingMedia)

## Storage
- Images are stored in a pluggable storage backend
- Local dev uses local filesystem, production uses object storage (e.g. S3, Cloudflare R2)
- Files are stored as `{media_folder}/{media_id}` - no path stored in DB, folder is config-driven