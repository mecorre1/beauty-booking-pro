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

### 1. Browse availability
- Client lands on a calendar view showing available slots
- Each slot displays its price and duration

### 2. Configure the session
- Service type (each has a base duration and price):
  - Regular haircut
  - Haircut + hairdressing
  - Color
- Gender: Male / Female (duration may vary by gender)
- Location: At the salon / At home
  - At-home adds an extra charge and extra internal buffer time (travel back and forth)
  - The buffer time is internal only, not shown to clients

### 3. Confirm booking
- Client fills in: name, email, phone
- Confirmation email sent on booking
- Client receives a link to edit or cancel their booking (no deadline)

### 4. Editing a booking
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

### Booking
- slot_id
- service_id
- price_at_booking (snapshot)
- salon_address_at_booking (snapshot)
- location: enum (salon | home)
- home_address (nullable)
- client_name, client_email, client_phone
- status: enum (confirmed | edited | cancelled)
- edit_token (unique link for client self-service)