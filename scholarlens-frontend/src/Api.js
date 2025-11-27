// Mock API with sample data - no backend needed!

const MOCK_PAPERS = [
    {
      paper_id: 1,
      title: "Attention Is All You Need",
      abstract: "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
      authors: ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
      published_date: "2017-06-12",
      primary_category: "cs.CL",
      categories: ["cs.CL", "cs.LG"],
      arxiv_id: "1706.03762",
      methods: ["Transformer", "Attention Mechanism", "Self-Attention"],
      datasets: ["WMT 2014"],
      citation_count: 15000
    },
    {
      paper_id: 2,
      title: "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
      abstract: "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.",
      authors: ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee"],
      published_date: "2018-10-11",
      primary_category: "cs.CL",
      categories: ["cs.CL"],
      arxiv_id: "1810.04805",
      methods: ["BERT", "Transformer", "Pre-training"],
      datasets: ["SQuAD", "GLUE"],
      citation_count: 12000
    },
    {
      paper_id: 3,
      title: "Deep Residual Learning for Image Recognition",
      abstract: "Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions.",
      authors: ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
      published_date: "2015-12-10",
      primary_category: "cs.CV",
      categories: ["cs.CV"],
      arxiv_id: "1512.03385",
      methods: ["ResNet", "CNN", "Residual Learning"],
      datasets: ["ImageNet"],
      citation_count: 20000
    },
    {
      paper_id: 4,
      title: "Generative Adversarial Networks",
      abstract: "We propose a new framework for estimating generative models via an adversarial process, in which we simultaneously train two models: a generative model G that captures the data distribution, and a discriminative model D that estimates the probability that a sample came from the training data rather than G.",
      authors: ["Ian Goodfellow", "Jean Pouget-Abadie", "Mehdi Mirza"],
      published_date: "2014-06-10",
      primary_category: "cs.LG",
      categories: ["cs.LG", "stat.ML"],
      arxiv_id: "1406.2661",
      methods: ["GAN", "Neural Networks"],
      datasets: ["MNIST", "CIFAR-10"],
      citation_count: 18000
    },
    {
      paper_id: 5,
      title: "You Only Look Once: Unified, Real-Time Object Detection",
      abstract: "We present YOLO, a new approach to object detection. Prior work on object detection repurposes classifiers to perform detection. Instead, we frame object detection as a regression problem to spatially separated bounding boxes and associated class probabilities.",
      authors: ["Joseph Redmon", "Santosh Divvala", "Ross Girshick"],
      published_date: "2015-06-08",
      primary_category: "cs.CV",
      categories: ["cs.CV"],
      arxiv_id: "1506.02640",
      methods: ["YOLO", "CNN", "Object Detection"],
      datasets: ["PASCAL VOC", "COCO"],
      citation_count: 25000
    }
  ];
  
  const MOCK_STATS = {
    status: "operational",
    databases: {
      postgresql: {
        connected: true,
        papers: 34,
        authors: 125
      },
      neo4j: {
        connected: true,
        nodes: 34
      },
      faiss: {
        connected: true,
        vectors: 150
      }
    },
    timestamp: Date.now()
  };
  
  // Simulate API delay
  const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  
  // Mock API functions
  export const healthCheck = async () => {
    await delay(300);
    return { data: { status: "healthy", service: "Mock API" } };
  };
  
  export const getSystemStatus = async () => {
    await delay(500);
    return { data: MOCK_STATS };
  };
  
  export const searchPapersSemantic = async (query, topK = 10) => {
    await delay(800);
    
    // Simple mock search - filter papers by query
    const searchLower = query.toLowerCase();
    const filtered = MOCK_PAPERS.filter(paper => 
      paper.title.toLowerCase().includes(searchLower) ||
      paper.abstract.toLowerCase().includes(searchLower) ||
      paper.methods.some(m => m.toLowerCase().includes(searchLower))
    );
  
    // Add similarity scores
    const results = filtered.map(paper => ({
      ...paper,
      similarity_score: Math.random() * 0.3 + 0.7 // Random score 0.7-1.0
    }));
  
    return {
      data: {
        results: results.slice(0, topK),
        total: results.length,
        query: query,
        search_type: "semantic",
        processing_time_ms: 123
      }
    };
  };
  
  export const searchPapersKeyword = async (query, page = 1, pageSize = 20) => {
    await delay(600);
    
    const searchLower = query.toLowerCase();
    const filtered = MOCK_PAPERS.filter(paper => 
      paper.title.toLowerCase().includes(searchLower) ||
      paper.abstract.toLowerCase().includes(searchLower)
    );
  
    return {
      data: {
        results: filtered,
        total: filtered.length,
        query: query,
        search_type: "keyword",
        processing_time_ms: 89
      }
    };
  };
  
  export const listPapers = async (page = 1, pageSize = 20) => {
    await delay(400);
    return {
      data: {
        papers: MOCK_PAPERS,
        total: MOCK_PAPERS.length,
        page: page,
        page_size: pageSize,
        total_pages: 1
      }
    };
  };
  
  export const getPaperById = async (paperId) => {
    await delay(400);
    const paper = MOCK_PAPERS.find(p => p.paper_id === parseInt(paperId));
    
    if (!paper) {
      throw new Error('Paper not found');
    }
    
    return { data: paper };
  };
  
  export default { 
    healthCheck, 
    getSystemStatus, 
    searchPapersSemantic, 
    searchPapersKeyword,
    listPapers,
    getPaperById
  };