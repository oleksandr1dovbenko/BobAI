<h1 align="center">🤖 BobAI</h1>

<p align="center">
  <a>
    <img src="https://img.shields.io/badge/Try_BobAI_Here!-success?style=for-the-badge&logo=github" alt="Live Demo">
  </a>
</p>

> **BobAI** is a fun, intelligent AI assistant built for my website and powered by the HCAI API.

<p align="center">
  <b><a href="https://oleksandr1dovbenko.github.io/BobAI/">Click here to try BobAI now!</a></b>
</p>

---

## 📖 The Backstory

I finally started this project thanks to **Hack Club** and their **Stardance** event. I've wanted to build something like this for a long time, but something was always holding me back. This event gave me the perfect reason to just go for it.

---

## Architecture Evolution

Building **BobAI** went through three different architectures to find the right balance between memory limits, hosting availability, and response speed.

### 1️⃣ First Plan: Fine-Tuned Model hosted on Hugging Face

* **Model:** Fine-tuned **Meta Llama 3.1 8B** using the **UltraFeedback** dataset to fit my exact needs.
* **Hosting Idea:** Wanted to host a FastAPI backend with a GGUF model on Hugging Face Spaces, but free Docker containers were discontinued.

### 2️⃣ Second Plan: Hack Club Nest + Custom Model

* **Hosting Idea (Nest):** Switched to **Hack Club Nest** to host the Python backend with the local model.
* **The Problem:** Running the fine-tuned model required at least 5 GB of RAM. My application for 6 GB was declined due to server resource exhaustion, making it impossible to host the custom fine-tuned model on this setup.

### 3️⃣ Current Architecture

To provide smooth performance without expensive hosting services, I decided to build the backend using the HCAI API.

```mermaid
flowchart LR
    A([Visitor's Browser]) <--> B[GitHub Pages<br>Static HTML/CSS/JS]
    B <--> C[(Hack Club Nest<br>HCAI + OpenRouter API)]
```

BobAI's current architecture, not the initial plan.

---

## 🎨 Frontend & Design

I am thankful to Claude for helping me build the user interface of this project. To be completely honest, without Claude's assistance, the website would have been empty, boring, and ugly!