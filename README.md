# BetterGut - AI-Powered Gut Health & Nutrition Tracker

A comprehensive mobile app (iOS & Android) that tracks nutrition, meals, and digestive health to provide personalized gut health insights using Llama 3 and RAG (Retrieval-Augmented Generation).

## 🎯 Features

### Core Functionality
- **Nutrition Tracking**: Log meals with AI-powered food recognition
- **Digestive Health Monitoring**: Track bowel movements with detailed health metrics
- **AI-Powered Insights**: Personalized recommendations using Llama 3 + RAG
- **Progress Analytics**: Visual dashboards for health trends and patterns
- **Smart Suggestions**: Meal recommendations based on gut health goals

### AI & Data Intelligence
- **Llama 3 LLM**: Advanced reasoning for health recommendations
- **RAG Pipeline**: Scientific literature integration for evidence-based advice
- **Computer Vision**: Food recognition and portion estimation
- **Personalization**: Adaptive recommendations based on user patterns

## 🏗️ Architecture

```
┌─────────────────┬─────────────────┬─────────────────┐
│   Mobile Apps   │   Backend API   │   AI Pipeline   │
│                 │                 │                 │
│ • Flutter iOS   │ • Node.js/Express │ • Llama 3     │
│ • Flutter Android│ • PostgreSQL    │ • RAG System   │
│ • Food Camera   │ • Docker        │ • Vector DB     │
│ • Health Metrics│ • REST API      │ • Web Crawlers  │
└─────────────────┴─────────────────┴─────────────────┘
```

## 🔬 RAG Data Sources

### Scientific Literature (API-First)
- **PubMed Central** - Biomedical research articles
- **Europe PMC** - European research database  
- **PLOS Journals** - Open access medical publications
- **Frontiers** - Nutrition & microbiology research

### Health Institutions (Sitemap Crawling)
- **NIH Health Information** - Evidence-based health guidance
- **CDC Nutrition** - Public health recommendations
- **Harvard Nutrition Source** - Expert nutrition advice
- **NCCIH** - Complementary health approaches

### Specialized Sources (Focused Crawling)
- **Gut Microbiota for Health** - Microbiome research
- **ISAPP** - Probiotics and prebiotics science
- **BZfE/DGE (Germany)** - European nutrition standards

## 📱 Mobile App Features

### Nutrition Tracking
- Photo-based food logging with AI recognition
- Barcode scanning for packaged foods
- Manual entry with smart autocomplete
- Meal timing and portion tracking
- Macro and micronutrient analysis

### Digestive Health Monitoring
- Bowel movement tracking (Bristol Stool Scale)
- Symptoms logging (bloating, pain, irregularity)
- Mood and energy correlation
- Medication and supplement tracking
- Hydration monitoring

### AI-Powered Insights
- Personalized gut health score
- Food sensitivity detection
- Optimal meal timing suggestions
- Probiotic/prebiotic recommendations
- Lifestyle factor correlations

## 🛠️ Tech Stack

### Mobile Development
- **Framework**: Flutter (iOS & Android)
- **State Management**: Riverpod/Bloc
- **Local Storage**: SQLite + Hive
- **Camera**: camera package for food photos
- **Charts**: fl_chart for analytics

### Backend Services
- **API**: Node.js + Express
- **Database**: PostgreSQL
- **Authentication**: JWT
- **File Storage**: Local/S3 for images
- **Containerization**: Docker + Docker Compose

### AI & ML Pipeline
- **LLM**: Llama 3 (via Ollama/Hugging Face)
- **Vector Database**: Chroma/Weaviate
- **Embeddings**: all-MiniLM-L6-v2
- **Web Crawling**: Scrapy + BeautifulSoup
- **RAG Framework**: LangChain

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Flutter SDK 3.x
- Docker & Docker Compose
- PostgreSQL (or use Docker)

### Backend Setup
```bash
cd backend
npm install
cp .env.example .env
# Configure your environment variables
docker-compose up -d  # Start PostgreSQL
npm run dev
```

### Mobile App Setup
```bash
cd mobile
flutter pub get
flutter run
```

### AI Pipeline Setup
```bash
cd ai-pipeline
pip install -r requirements.txt
python crawl_health_data.py  # Populate RAG database
python start_llm_service.py  # Start Llama 3 service
```

## 📊 Data Privacy & Security

- **HIPAA Considerations**: Health data encryption and secure storage
- **Local Processing**: Sensitive AI inference on-device when possible
- **Data Anonymization**: Personal identifiers removed from research data
- **User Control**: Complete data export and deletion capabilities

## 🔄 Development Roadmap

### Phase 1: Core App (Current)
- [x] Backend API development
- [x] Database schema design
- [ ] Flutter app foundation
- [ ] Basic nutrition tracking
- [ ] User authentication

### Phase 2: AI Integration
- [ ] RAG pipeline implementation
- [ ] Health data crawling
- [ ] Llama 3 integration
- [ ] Basic recommendations

### Phase 3: Advanced Features
- [ ] Computer vision for food recognition
- [ ] Advanced analytics dashboard
- [ ] Social features (optional)
- [ ] Wearable device integration

### Phase 4: Research & Validation
- [ ] Clinical validation studies
- [ ] User experience optimization
- [ ] Performance monitoring
- [ ] App store deployment

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This app is for informational purposes only and should not replace professional medical advice. Always consult healthcare providers for medical concerns.