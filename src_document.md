# AI Smart Local Commerce Communication Platform

## PRD + CRC (Component Responsibility Collaboration) Document

---

# 1. Product Overview

## Objective

Build an **AI-powered communication layer for commerce platforms** that automatically communicates with customers when order events occur.

The system:

1. Receives order events from platforms
2. Initiates **AI-powered voice calls**
3. Handles **dynamic customer speech**
4. If the call fails → sends **WhatsApp message fallback**

Platforms supported:

* Shopify
* WooCommerce

---

# 2. Problem Statement

Local businesses often face issues like:

* Delivery failures
* Order confirmations
* Return processing
* Payment reminders

These require **manual communication**, which causes:

* Delays
* Operational cost
* Poor customer experience

The system automates communication using **AI voice + WhatsApp fallback**.

---

# 3. Core Workflow

### Primary Flow

```
Order Event
     ↓
AI Voice Call
     ↓
Customer Response
     ↓
Order Status Update
```

### Fallback Flow

```
Order Event
     ↓
AI Voice Call
     ↓
Call Failed
     ↓
Send WhatsApp Message
```

---

# 4. Functional Requirements

## FR1 — Order Event Integration

System must receive order events from:

* Shopify Webhooks
* WooCommerce Webhooks

Required order data:

```
order_id
customer_name
customer_phone
order_status
items
timestamp
platform
```

---

## FR2 — Event Processing

Supported triggers:

```
delivery_failed
order_created
payment_pending
order_returned
order_delivered
```

Each event triggers communication.

---

## FR3 — AI Voice Communication

System must:

* initiate phone call
* play AI-generated speech
* capture speech response

Example call flow:

```
Hello Rahul,

Your order delivery failed today.
Would you like to reschedule delivery?

Say YES or NO.
```

---

## FR4 — Speech Recognition

System must process:

```
Yes
No
Deliver tomorrow
Cancel order
Call later
```

Speech pipeline:

```
voice → speech-to-text → intent detection → action
```

---

## FR5 — WhatsApp Fallback

If voice call fails:

Trigger WhatsApp message.

Example:

```
Hi Rahul,

Your order delivery failed today.

Reply YES to reschedule delivery.
```

---

## FR6 — Vendor Dashboard

Dashboard must show:

* orders
* events
* call logs
* customer responses

---

# 5. Non Functional Requirements

### NFR1 — Rapid Development

System must be deployable in **1 day**.

---

### NFR2 — Platform Independent

Must support multiple commerce platforms.

---

### NFR3 — Reliable Communication

Fallback ensures communication always happens.

---

### NFR4 — Minimal Infrastructure

Avoid heavy infrastructure.

---

# 6. Technology Stack

## Backend

Framework options:

Option 1

FastAPI

Option 2

Node.js Express

Recommended:

```
FastAPI
```

---

## Database

```
PostgreSQL
```

Stores:

* orders
* events
* communication logs

---

# 7. External Integrations

---

# 7.1 Voice API

Recommended:

**Twilio**

Capabilities:

* phone calls
* speech recognition
* text-to-speech
* free trial credits

---

# 7.2 Speech Recognition

Options:

1. Twilio speech recognition
2. Google Speech API
3. Deepgram

Recommended:

```
Twilio Speech Recognition
```

---

# 7.3 Text to Speech

Options:

* ElevenLabs
* Google TTS
* Amazon Polly

Recommended:

```
ElevenLabs
```

Reason:

Best voice quality.

---

# 7.4 WhatsApp Messaging

Options:

1. **Meta**
2. Twilio WhatsApp API
3. MessageBird

Recommended:

```
Meta WhatsApp Cloud API
```

Reason:

Free tier + official API.

---

# 7.5 Commerce Integration

Shopify integration via:

```
Shopify Webhooks
```

WooCommerce integration via:

```
WooCommerce Webhooks
```

---

# 8. System Architecture

```
Shopify / WooCommerce
        │
        │ Webhooks
        ▼
Order Event API
        │
        ▼
Event Processing Engine
        │
        ▼
Communication Engine
        │
 ┌───────────────┐
 │               │
 ▼               ▼
Voice API    WhatsApp API
```

---

# 9. CRC Model (Component Responsibility Collaboration)

---

# Component 1 — Order Integration Service

### Responsibilities

* receive webhook events
* normalize order data
* store orders

### Collaborates With

* Event Processing Engine
* Database

---

# Component 2 — Event Processing Engine

### Responsibilities

* detect event triggers
* invoke communication workflows

Example:

```
delivery_failed → call_customer
```

### Collaborates With

* Communication Engine
* Rule Engine

---

# Component 3 — Communication Engine

### Responsibilities

* initiate voice calls
* process responses
* trigger fallback

### Collaborates With

* Voice API
* WhatsApp API

---

# Component 4 — AI Conversation Engine

### Responsibilities

* speech recognition
* intent detection
* generate responses

### Collaborates With

* Communication Engine

---

# Component 5 — Fallback Manager

### Responsibilities

Detect call failure and send WhatsApp message.

Trigger conditions:

```
call_not_answered
call_failed
call_timeout
```

### Collaborates With

* WhatsApp API

---

# Component 6 — Vendor Dashboard

### Responsibilities

* display logs
* show orders
* track communication

### Collaborates With

* Database

---

# 10. Data Model

---

## Orders Table

```
order_id
platform
customer_name
customer_phone
status
created_at
```

---

## Events Table

```
event_id
order_id
event_type
timestamp
```

---

## Communications Table

```
communication_id
order_id
type
status
response
timestamp
```

---

# 11. Voice Interaction Pipeline

```
Call Initiated
      ↓
TTS Prompt
      ↓
Customer Speech
      ↓
Speech to Text
      ↓
Intent Detection
      ↓
Response
```

---

# 12. Fallback Logic

### Trigger Conditions

```
call_not_answered
call_failed
voicemail_detected
```

### Fallback Action

Send WhatsApp message.

---

# 13. Hackathon Build Plan (1 Day)

### Hour 1-2

Setup backend and database.

---

### Hour 3-4

Integrate Shopify and WooCommerce webhooks.

---

### Hour 5-6

Integrate Twilio voice API.

---

### Hour 7-8

Implement AI voice interaction.

---

### Hour 9-10

Add WhatsApp fallback.

---

### Hour 11-12

Build dashboard and demo flow.

---

# 14. Demo Scenario

Judge demo:

1. Create order in Shopify
2. Trigger delivery failure
3. System calls customer
4. Customer response processed
5. If call ignored → WhatsApp sent

---

# 15. Key Innovation

The platform acts as an:

**AI Customer Communication Layer for Commerce**

It automates:

* delivery confirmation
* order recovery
* return communication
* payment reminders

