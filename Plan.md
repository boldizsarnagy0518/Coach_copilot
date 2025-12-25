# **Coach Copilot: Master Strategic Plan & Technical Roadmap**

This document outlines the architectural and functional development of the **Coach Copilot**, a next-generation AI assistant for Powerlifting coaches and athletes.

## **1\. Project Vision**

To create a "Digital Twin" of a Powerlifting Coach that combines the precision of Data Engineering with specialized domain expertise. The system will bridge the gap between static training plans (Google Sheets) and dynamic expert guidance (YouTube/Coaching Docs).

## **2\. The Bleeding-Edge Tech Stack**

To ensure the highest level of reliability and "intelligence," the project utilizes the most modern AI development patterns:

* **Orchestration:** **LangGraph** (State-based Agentic Workflows). Unlike linear chains, this allows for cycles, human-in-the-loop interactions, and complex decision-making.  
* **Agent Pattern:** **ReAct (Reasoning \+ Acting)**. The agent determines which tool to use based on the user's intent.  
* **RAG Engine:** **Multi-modal & Semantic RAG**.  
  * *Semantic Chunking:* Breaking down rulebooks by logic rather than character count.  
  * *YouTube Transcripts:* Leveraging the YoutubeLoader for instructional content.  
* **Environment:** **uv** for ultra-fast Python package management and **FastAPI** for high-performance backend serving.  
* **Data Storage:** **Vector Databases (FAISS/Chroma)** for unstructured data and **Google Sheets API** for structured training logs.

## **3\. Phased Roadmap (From MVP to Expert)**

### **Phase 1: The Informed Observer (Read-Only MVP)**

**Goal:** Establish trust by accurately retrieving data.

* **Capabilities:** \* "What is my workout today?" \-\> Reads Google Sheets and summarizes.  
  * "What are the IPF rules for the bench press?" \-\> Retrieves from technical rulebooks via RAG.  
* **Tech Focus:** Basic LangGraph implementation with a SearchTool and SheetsReaderTool.

### **Phase 2: The Domain Expert (Calculators & Multimedia)**

**Goal:** Add specialized math and your personal coaching voice.

* **Capabilities:**  
  * **Mathematical Precision:** Custom Python Tools for E1RM, Wilks/IPF GL scores, and Plate Loading (calculating exact bar weight).  
  * **Visual Integration:** Linking your YouTube tutorials. "How do I fix my squat depth?" \-\> Returns your specific video link \+ summary of your cues.  
* **Tech Focus:** Tool-calling optimization and YouTube Transcript RAG.

### **Phase 3: The Adaptive Strategist (Agentic Writing)**

**Goal:** Intelligent rescheduling and plan modification.

* **Capabilities:**  
  * **Plan Rescheduling:** "I can only train 2 days this week." \-\> The agent analyzes your SBD (Squat, Bench, Deadlift) priorities, condenses the 4-day block into 2 days, and **updates the Google Sheet**.  
  * **Injury Management:** If "pain" is mentioned, the agent cross-references your injury protocols and suggests load reductions.  
* **Tech Focus:** Advanced LangGraph nodes for "Plan Logic" and Google Sheets Write-access tools.

## **4\. System Architecture (Data Flow)**

1. **Input Analyzer Node:** Determines if the user wants information (RAG), a calculation (Math Tool), or a modification (Logic Node).  
2. **Context Aggregator:** Gathers live data from the athlete's Google Sheet and historical data from the Coach’s Knowledge Base.  
3. **The Reasoning Node:** A high-level LLM node that maps out the "Coach's Decision" based on your specific coaching methodology found in your Docs and YouTube videos.  
4. **Tool Executor:** Executes Python code for math or API calls for Google Sheets.  
5. **Multimodal Output Node:** Constructs a response containing human-like coaching advice, updated sheet links, and relevant YouTube tutorial cards.

