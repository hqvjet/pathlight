# Thesis Presentation within 15 mins (12 talking, 3 demo)
## Beginning (30 secs)
### Purpose: The greeting to examination board and opening to topic
I would like to extend my warmest greetings and best wishes for health to the Examination Board and everyone present here today. It is a great honor for me to be here today. My name is Hoang Quoc Viet and he is Ho Ngoc Hoa, my teammate. I am excited to present my thesis titled: PathLight, a self-directed learning system.
## Idea Introduction (2 mins)
### Purpose: To introduce the motivation, the expensive points and brief overview of PathLight
### Pre: Motivation
Let’s start with a reality we all face. In this digital era, accessing information is easy. We have millions of PDFs, slides, and textbooks.

But here lies the 'Self-Directed Learning Paradox': We are drowning in content but starving for structured knowledge.

The real problem today isn't finding materials; it is consuming them effectively. Self-study is often passive, lonely, and lacks guidance, leading to very high dropout rates.

So, I asked myself a practical question: 'How can we use AI to instantly transform a static, boring PDF into an interactive, gamified course?'

That brings us to Pathlight. It is not just a storage system; it is an automated pipeline designed to solve this exact inefficiency

Moreover, Looking at the EdTech landscape, specifically in Vietnam—one of the top 10 fastest-growing markets—we are seeing a massive shift.

We are moving from Education 1.0, where systems simply hosted files for users to download, to Education 2.0, where users demand interaction and personalization.

However, the current challenge is Scalability. Creating a high-quality, interactive course manually takes weeks of effort from teachers. It is a slow and expensive bottleneck.

My goal with Pathlight was to break this bottleneck.

By leveraging Generative AI and RAG, I built a system that automates this entire workflow—reducing the time from 'Raw Data' to 'Ready-to-Learn Course' from weeks to just minutes

### Post: Brief Overview
Before going into the diagrams, let me explain the core concept of Pathlight simply.

Imagine you have a long, heavy PDF document. Reading it alone is difficult and boring. This is passive reading.

Pathlight solves this by acting like a Digital Tutor.

Input: You upload your file and choose your settings—like your 'Role' or 'Learning Style'.

Processing: The system analyzes only that specific file. It does not create random content. It strictly extracts knowledge from your document.

Output: It converts that static file into a Guided Course with chapters, quizzes, and progress tracking.

So, simply put: We turn a raw file into a structured class.

Instead of just scrolling through pages, users now have a roadmap to follow and quizzes to practice.

To make this workflow possible, let’s look at the Functional Overview...

## System Introduction (2 mins 30 secs)
### Purpose: To show examination board the highlevel system design (usecase, class), that let them know our team not stop in coding only, but we know how to prepare our idea and design them.
### Infrastructure Solution
"Moving to the System Design, I want to start with the foundation. To ensure scalability, I did not just build a web app; I architected a Cloud-Native System on AWS.

As you can see in this architecture:

Security: I divided the network into a Public Subnet for the Frontend and a Private Subnet for the Database and Vector Store, ensuring no direct outside access to sensitive data.

Performance: Crucially, I used an Event-Driven Architecture with AWS SQS. All heavy AI tasks are pushed to a Queue and processed asynchronously. This ensures the user experience is zero-latency, even under heavy load

### Usecase Part
To bring this 'Digital Tutor' concept to life, I designed a functional ecosystem that involves 4 key actors.

It is not just about the student; it requires a complete system to operate smoothly.

1. First, The User: This is the learner. They interact with the core features: uploading documents, defining their learning path, and taking quizzes.

2. Second, The System Actor: This is the most special part. Unlike traditional apps that wait for human input, Pathlight works in the background. The 'System' actor automatically handles heavy tasks like Generating Courses and Sending Notifications without making the user wait. It acts like the invisible engine of the platform.

3. Third, The Admin: To make this project sustainable in the real world, the Admin oversees user management and monitors Operational Costs (like AWS usage).

4. Finally, The Guest: Representing new visitors entering the platform.

So, we have a system with diverse actors and automated processes. To handle this complexity strictly and logically, I needed a robust data structure. Let’s move to the Class Design...

### Class Part
1. First, The Content Hierarchy (Course Service):Instead of storing loose files, I designed a strict hierarchy: Course -> Lesson -> Assessment. A Course owns many Lessons, and each Lesson owns specific Assessments.This structure ensures the generated content is not random; it follows a logical path, just like a real textbook chapter.

2. Second, The User Separation (User Service):I separated the User Identity from the Gamification Profile. 'User' stores login info, while 'User Profile' stores EXP, Levels, and Streaks.This decoupling keeps the login process fast and secure, even if the gamification data becomes heavy.

3. Third, The AI Orchestration (Agentic Service):To control the AI, I implemented an Orchestrator Agent. It acts like a manager, coordinating specialized agents like the Planner and Test Creator.This ensures the AI output is always structured and valid before saving to the database.With this solid foundation, let’s dive into the Key Features
## Deep Dive Into Key Features (5 mins)
### Purpose: Deep describe the 3 MVP features, the generation workflow, the ingestion workflow and the recommendation system
### Generation workflow
Now, let’s move to the Core Technology—how we actually generate a high-quality course.

Many people think AI generation is just sending one big prompt to ChatGPT. But for an educational system, that is too risky and inaccurate.

Instead, I implemented a Multi-Agent Orchestration architecture. Think of it as a team of specialized experts working together under one manager:

The Orchestrator (The Manager): [Point to the top box] It controls the flow and ensures no step is skipped.

The Plan Agent (The Architect): It reads the documents to design a logical Syllabus first. It decides what to teach and in what order.

The Lesson Agent (The Writer): Once the plan is approved, this agent writes the detailed content for each lesson using Context-Aware Retrieval.

The Assessment Agent (The Examiner): Simultaneously, this agent creates quizzes aligned with Bloom’s Taxonomy to test the user's understanding.

Finally, The JSON Constructor: It ensures the output is strictly formatted so the system can render it without errors.

This collaboration ensures the course is structured, logical, and technically robust.

### Ingestion workflow
But for those agents to work correctly, they need high-quality data. This brings us to the Ingestion Pipeline.

As the saying goes: 'Garbage in, garbage out.' If the input is messy, the course will be messy. So, I built a strict pipeline to process user documents:

Parsing: 
- For PDFs, we use an OCR model (Tesseract 4) to handle scanned documents or complex layouts.
- For Office files (DOCX, PPTX), we extract text directly from their XML structure using specialized libraries (python-docx, python-pptx). This ensures 100% accuracy and is much faster than OCR

Semantic Chunking:  We don't just cut text randomly. We use Semantic Chunking to keep related ideas together. For example, a paragraph about 'CNNs' stays in one chunk.

Embedding: Finally, we convert these chunks into Vectors (mathematical numbers) and store them in the Vector Database.

Why is this important? This allows the AI to search for exact information from your specific file when generating lessons. It guarantees that the AI sticks to the source material and minimizes hallucinations

### Recommendation System
Finally, a great education system doesn't just teach; it guides. That’s why I built a Personalized Recommendation Engine.

We don't use simple keyword matching. We use Semantic Vectorization to understand the user's true interests. The process works in 3 steps:

Course Fingerprinting: First, for every public course, I combine its Title and Description and convert them into a 'Course Vector' using our embedding model.

User Profiling: To understand the learner, I calculate a 'User Vector'. This is done by taking the mathematical average of all the vectors of the courses they have already studied. This creates a dynamic profile that evolves as they learn.

Matching: Finally, the system compares this User Vector against all Public Course Vectors using Cosine Similarity to rank the Top-K most relevant courses.

This ensures that if a user loves 'Deep Learning', the system won't suggest 'Basic Accounting'—it will intelligently recommend 'Advanced Neural Networks' instead
## Implemented Modules (1 mins 30 secs)
### Purpose: To demostrate our implemented system, show the modules that we have done and describe the infrastructure solution

### Implemented modules:
Moving to the Implementation, we successfully translated these complex logical flows into a seamless MVP.

1. First, the Course Generation Flow:

[Show Sequence Diagram + Create Course UI] Looking at the Sequence Diagram, you can see the complex handshake between the User, SQS, and our AI Agents. We abstracted all this complexity behind a simple 'One-Click' UI. The user just inputs a prompt, and the system orchestrates the heavy lifting in the background.

2. Second, the Learning & Assessment Loop:

[Show Activity Diagram + Quiz UI] For the core learning experience, we strictly implemented the 'Lock-step' logic shown in this Activity Diagram. On the UI, this translates to a secure testing environment where users must pass the Server-Side Grading verification before unlocking the next lesson.

3. Third, Real-time Gamification:

[Show Dashboard UI] And all progress is synchronized instantly to this User Dashboard, tracking EXP and Streaks in real-time

## Demo (3 mins)
### Show video
## Limitations & Future Works (30 secs)
### Purpose: show them our broad perspective + honestly
### Limitation:
After the demo, while I am proud of the MVP, I must address the Technical Realities honestly.

1. First, The 'Garbage In, Garbage Out' Problem: Even with RAG, the system is strictly dependent on the input quality. If a user uploads a poorly scanned or nonsensical PDF, the AI struggles to generate a perfect course. 
2. Second, Operational Cost: Currently, relying on commercial APIs like OpenAI is expensive for scale. It works for a thesis, but for a startup, the cost-per-user is still high. 
3. Third, Evaluation Scale: The current results are based on pilot testing. We haven't stress-tested it with thousands of concurrent users yet
### Future Works:
However, these limitations define my roadmap for the future.

To solve the Cost issue: I plan to migrate from GPT-4 to Self-Hosted Open Source Models (like Llama 3 or Mistral) optimized specifically for education. This will drastically reduce costs and ensure data privacy.

To improve Learning: I want to upgrade the recommendation engine to Adaptive Sequencing. Instead of a fixed path, the system will dynamically adjust the curriculum based on the student's weak points in real-time.

Essentially, the goal is to evolve Pathlight from a 'Course Generator' into a truly 'Personalized AI Tutor

## Ending (30 secs)
To conclude, Pathlight started with a simple question: 'How can we learn faster in an age of information overload?'

With this thesis, I believe I have laid the technical foundation for the answer. It is not just about automation; it is about empowering self-directed learners to own their knowledge.

Thank you, the Examination Board and everyone, for listening. I am now ready for your questions and feedback.

I have also deployed the system live. You can scan this QR code to experience Pathlight on your own devices during the Q&A session
