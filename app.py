"""
ScholarLens - AI-Powered Research Intelligence Platform
Main Streamlit application
"""

import streamlit as st
import os
from datetime import datetime

st.set_page_config(
    page_title="ScholarLens",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

from models import init_db, get_session, Paper, Author, Method, Dataset, Institution, PaperChunk, Note, Flashcard, SavedQuery, ReadingList, paper_authors, paper_methods, paper_datasets
from utils.pdf_processor import extract_text_from_pdf, chunk_text, get_section_for_chunk
from utils.ner_extractor import extract_entities, build_method_prerequisites
from utils.openai_helper import (
    is_available as openai_available,
    generate_summary,
    answer_question,
    generate_flashcards,
    generate_quiz,
    generate_policy_brief,
    generate_analogy,
    extract_key_insights
)
from utils.semantic_search import PaperSearchIndex, find_similar_papers
from utils.graph_builder import (
    build_knowledge_graph,
    build_method_dag,
    create_plotly_graph,
    create_method_dag_visualization,
    build_coauthorship_network,
    calculate_graph_metrics,
    find_collaboration_opportunities
)
from utils.analytics import (
    get_top_coauthorship_pairs,
    get_trending_topics_over_time,
    get_papers_per_institution,
    get_research_growth_by_field,
    get_top_authors_by_publication,
    get_most_used_datasets,
    get_collaboration_network_density,
    get_emerging_methods,
    get_dataset_method_cooccurrence,
    get_yearly_publication_stats,
    get_method_category_distribution,
    get_summary_statistics
)
from utils.arxiv_pubmed import ArxivAPI, PubMedAPI, search_papers
from utils.topic_modeling import cluster_papers, extract_topics, PaperClusterer
from utils.trend_forecasting import (
    analyze_method_trends,
    identify_emerging_methods,
    identify_declining_methods,
    generate_forecast_summary,
    create_timeline_data
)
from utils.export_utils import (
    generate_markdown_review,
    generate_latex_review,
    generate_bibtex,
    generate_plain_text_review,
    generate_csv_export,
    create_summary_statistics as create_export_stats
)
from utils.theme import register_plotly_theme, get_css, hero_banner, NODE_TYPE_COLORS
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import networkx as nx

register_plotly_theme()
init_db()

if 'search_index' not in st.session_state:
    st.session_state.search_index = PaperSearchIndex()
if 'current_paper_id' not in st.session_state:
    st.session_state.current_paper_id = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


def main():
    st.markdown(get_css(), unsafe_allow_html=True)
    st.sidebar.title("ScholarLens")
    st.sidebar.markdown("*AI-Powered Research Intelligence*")
    st.sidebar.markdown("---")
    
    pages = {
        "Upload Papers": page_upload,
        "Knowledge Graph": page_knowledge_graph,
        "Research Q&A": page_qa,
        "Multi-Audience Summaries": page_summaries,
        "Analytics Dashboard": page_analytics,
        "Learning Mode": page_learning,
        "Research Workspace": page_workspace
    }
    
    selection = st.sidebar.radio("Navigate", list(pages.keys()))
    
    st.sidebar.markdown("---")
    session = get_session()
    stats = get_summary_statistics(session)
    session.close()
    
    st.sidebar.markdown("### Quick Stats")
    st.sidebar.metric("Papers", stats['total_papers'])
    st.sidebar.metric("Authors", stats['total_authors'])
    st.sidebar.metric("Methods", stats['total_methods'])
    st.sidebar.metric("Datasets", stats['total_datasets'])
    
    if not openai_available():
        st.sidebar.warning("OpenAI API key not configured. Some AI features will be limited.")
    
    pages[selection]()


def page_upload():
    """ScholarLens - Paper Upload"""
    st.markdown(
        hero_banner("ScholarLens", "Making Research Intuitive, Interactive, and Insightful"),
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload Research Papers")
        
        uploaded_files = st.file_uploader(
            "Upload PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload one or more research papers in PDF format"
        )
        
        if uploaded_files:
            if st.button("Process Papers", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                session = get_session()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing: {uploaded_file.name}")
                    
                    result = extract_text_from_pdf(uploaded_file)
                    
                    if result['success']:
                        entities = extract_entities(result['text'])
                        
                        extracted_year = result['metadata'].get('year')
                        if not extracted_year:
                            import re
                            from datetime import datetime
                            year_match = re.search(r'\b(20[0-2][0-9])\b', result['text'][:5000])
                            if year_match:
                                extracted_year = int(year_match.group(1))
                            else:
                                extracted_year = datetime.now().year
                        
                        paper = Paper(
                            title=result['metadata'].get('title', uploaded_file.name.replace('.pdf', '')),
                            abstract=result['sections'].get('abstract', ''),
                            content=result['text'][:50000],
                            source='pdf',
                            year=extracted_year,
                            doi=result['metadata'].get('doi'),
                            pdf_path=uploaded_file.name,
                            topics=[m['name'] for m in entities['methods'][:5]]
                        )
                        session.add(paper)
                        session.flush()
                        
                        for author_data in entities['authors'][:10]:
                            author = session.query(Author).filter_by(name=author_data['normalized_name']).first()
                            if not author:
                                author = Author(name=author_data['normalized_name'])
                                session.add(author)
                                session.flush()
                            paper.authors.append(author)
                        
                        for method_data in entities['methods'][:20]:
                            method = session.query(Method).filter_by(name=method_data['name']).first()
                            if not method:
                                method = Method(
                                    name=method_data['name'],
                                    category=method_data.get('category', 'unknown'),
                                    usage_count=1
                                )
                                session.add(method)
                            else:
                                method.usage_count += 1
                            session.flush()
                            paper.methods.append(method)
                        
                        for dataset_data in entities['datasets'][:20]:
                            dataset = session.query(Dataset).filter_by(name=dataset_data['name']).first()
                            if not dataset:
                                dataset = Dataset(
                                    name=dataset_data['name'],
                                    domain=dataset_data.get('domain', 'unknown'),
                                    usage_count=1
                                )
                                session.add(dataset)
                            else:
                                dataset.usage_count += 1
                            session.flush()
                            paper.datasets.append(dataset)
                        
                        for inst_data in entities['institutions'][:10]:
                            institution = session.query(Institution).filter_by(name=inst_data['name']).first()
                            if not institution:
                                institution = Institution(
                                    name=inst_data['name'],
                                    type=inst_data.get('type', 'unknown')
                                )
                                session.add(institution)
                                session.flush()
                            for author in paper.authors:
                                if institution not in author.institutions:
                                    author.institutions.append(institution)
                        
                        chunks = chunk_text(result['text'], chunk_size=1000, overlap=200)
                        for chunk in chunks:
                            paper_chunk = PaperChunk(
                                paper_id=paper.id,
                                chunk_index=chunk['index'],
                                content=chunk['content'],
                                section=get_section_for_chunk(chunk['content'], result['sections'])
                            )
                            session.add(paper_chunk)
                        
                        st.session_state.search_index.index_paper(
                            paper.id,
                            paper.title,
                            paper.abstract,
                            chunks,
                            [m['name'] for m in entities['methods']]
                        )
                        
                        session.commit()
                        st.success(f"Processed: {uploaded_file.name}")
                    else:
                        st.error(f"Failed to process {uploaded_file.name}: {result.get('error', 'Unknown error')}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                session.close()
                status_text.text("Processing complete!")
                st.balloons()
    
    with col2:
        st.subheader("Recent Papers")
        session = get_session()
        recent_papers = session.query(Paper).order_by(Paper.created_at.desc()).limit(5).all()
        
        for paper in recent_papers:
            with st.expander(paper.title[:50] + "..." if len(paper.title) > 50 else paper.title):
                st.write(f"**Year:** {paper.year or 'Unknown'}")
                st.write(f"**Authors:** {', '.join([a.name for a in paper.authors[:3]])}")
                st.write(f"**Methods:** {', '.join([m.name for m in paper.methods[:3]])}")
        
        session.close()
    
    st.markdown("---")
    st.subheader("Manage Papers")
    st.markdown("*Delete papers from your library*")
    
    session = get_session()
    all_papers = session.query(Paper).order_by(Paper.created_at.desc()).all()
    
    if all_papers:
        if 'papers_to_delete' not in st.session_state:
            st.session_state.papers_to_delete = []
        
        paper_options = {f"{p.title[:60]}... (ID: {p.id})" if len(p.title) > 60 else f"{p.title} (ID: {p.id})": p.id for p in all_papers}
        
        selected_papers = st.multiselect(
            "Select papers to delete",
            options=list(paper_options.keys()),
            key="delete_paper_select"
        )
        
        if selected_papers:
            st.warning(f"You have selected {len(selected_papers)} paper(s) for deletion.")
            
            col_del1, col_del2 = st.columns(2)
            
            with col_del1:
                if st.button("Delete Selected Papers", type="primary"):
                    deleted_count = 0
                    for paper_label in selected_papers:
                        paper_id = paper_options[paper_label]
                        paper_to_delete = session.query(Paper).filter_by(id=paper_id).first()
                        if paper_to_delete:
                            session.query(PaperChunk).filter_by(paper_id=paper_id).delete()
                            session.query(Note).filter_by(paper_id=paper_id).delete()
                            session.query(ReadingList).filter_by(paper_id=paper_id).delete()
                            session.query(Flashcard).filter_by(paper_id=paper_id).delete()
                            
                            paper_to_delete.authors = []
                            paper_to_delete.methods = []
                            paper_to_delete.datasets = []
                            session.flush()
                            
                            session.delete(paper_to_delete)
                            deleted_count += 1
                    
                    from sqlalchemy import func
                    orphan_authors = session.query(Author).filter(
                        ~Author.id.in_(
                            session.query(paper_authors.c.author_id)
                        )
                    ).all()
                    for author in orphan_authors:
                        session.delete(author)
                    
                    orphan_methods = session.query(Method).filter(
                        ~Method.id.in_(
                            session.query(paper_methods.c.method_id)
                        )
                    ).all()
                    for method in orphan_methods:
                        session.delete(method)
                    
                    orphan_datasets = session.query(Dataset).filter(
                        ~Dataset.id.in_(
                            session.query(paper_datasets.c.dataset_id)
                        )
                    ).all()
                    for dataset in orphan_datasets:
                        session.delete(dataset)
                    
                    session.commit()
                    st.success(f"Deleted {deleted_count} paper(s) and cleaned up orphaned data!")
                    st.rerun()
            
            with col_del2:
                if st.button("Delete ALL Papers", type="secondary"):
                    st.session_state.confirm_delete_all = True
        
        if st.session_state.get('confirm_delete_all', False):
            st.error("Are you sure you want to delete ALL papers? This cannot be undone!")
            col_confirm1, col_confirm2 = st.columns(2)
            with col_confirm1:
                if st.button("Yes, Delete All"):
                    for paper in all_papers:
                        session.query(PaperChunk).filter_by(paper_id=paper.id).delete()
                        session.query(Note).filter_by(paper_id=paper.id).delete()
                        session.query(ReadingList).filter_by(paper_id=paper.id).delete()
                        session.query(Flashcard).filter_by(paper_id=paper.id).delete()
                        paper.authors = []
                        paper.methods = []
                        paper.datasets = []
                    session.flush()
                    session.query(Paper).delete()
                    
                    session.query(Author).delete()
                    session.query(Method).delete()
                    session.query(Dataset).delete()
                    session.query(Institution).delete()
                    
                    session.commit()
                    st.session_state.confirm_delete_all = False
                    st.success("All papers and associated data deleted!")
                    st.rerun()
            with col_confirm2:
                if st.button("Cancel"):
                    st.session_state.confirm_delete_all = False
                    st.rerun()
    else:
        st.info("No papers in your library yet.")
    
    session.close()
    
    st.markdown("---")
    st.subheader("Semantic Search")
    
    search_query = st.text_input("Search papers by concept, method, or keyword")
    
    if search_query:
        results = st.session_state.search_index.search_all(search_query, top_k=5)
        
        if results:
            st.write(f"Found {len(results)} relevant results:")
            for result in results:
                with st.expander(f"Score: {result['score']:.3f} | {result.get('source', 'content')}"):
                    st.write(result['content'][:500] + "...")
        else:
            session = get_session()
            papers = session.query(Paper).all()
            paper_dicts = [{'id': p.id, 'title': p.title, 'abstract': p.abstract, 'content': p.content} for p in papers]
            session.close()
            
            if paper_dicts:
                similar = find_similar_papers(search_query, paper_dicts, top_k=3)
                if similar:
                    st.write("Similar papers found:")
                    for paper in similar:
                        st.write(f"- {paper['title']} (Score: {paper.get('similarity_score', 0):.3f})")
    
    st.markdown("---")
    st.subheader("Fetch from Open-Access Sources")
    st.markdown("*Search arXiv and PubMed for research papers*")
    
    if 'api_search_results' not in st.session_state:
        st.session_state.api_search_results = []
    if 'imported_papers' not in st.session_state:
        st.session_state.imported_papers = set()
    
    if st.session_state.imported_papers:
        st.success(f"Successfully imported {len(st.session_state.imported_papers)} paper(s) to your library!")
        if st.button("Clear Import Messages"):
            st.session_state.imported_papers = set()
            st.rerun()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        api_query = st.text_input("Search arXiv/PubMed", placeholder="e.g., transformer attention mechanism")
    
    with col2:
        source = st.selectbox("Source", ["arXiv", "PubMed", "Both"])
        max_results = st.slider("Max results", 5, 100, 10)
    
    if api_query and st.button("Search External Sources", type="secondary"):
        with st.spinner("Searching..."):
            sources = []
            if source in ["arXiv", "Both"]:
                sources.append("arxiv")
            if source in ["PubMed", "Both"]:
                sources.append("pubmed")
            
            results = search_papers(api_query, sources=sources, max_results=max_results)
            st.session_state.api_search_results = results
            st.session_state.imported_papers = set()
    
    if st.session_state.api_search_results:
        results = st.session_state.api_search_results
        st.info(f"Found {len(results)} papers")
        
        for i, paper in enumerate(results):
            paper_id = paper.get('arxiv_id') or paper.get('pmid') or f"paper_{i}"
            is_imported = paper_id in st.session_state.imported_papers
            
            title_display = paper.get('title', 'Untitled')[:80]
            if is_imported:
                title_display = f"✓ {title_display}"
            
            with st.expander(f"{title_display}..."):
                st.write(f"**Source:** {paper.get('source', 'Unknown').upper()}")
                st.write(f"**Year:** {paper.get('year', 'Unknown')}")
                
                if paper.get('authors'):
                    author_names = [a.get('name', '') for a in paper['authors'][:5]]
                    st.write(f"**Authors:** {', '.join(author_names)}")
                
                if paper.get('abstract'):
                    st.write(f"**Abstract:** {paper['abstract'][:500]}...")
                
                if paper.get('url'):
                    st.markdown(f"[View Paper]({paper['url']})")
                
                if is_imported:
                    st.success("Already imported to library")
                else:
                    if st.button("Import to Library", key=f"import_{i}"):
                        try:
                            session = get_session()
                            
                            new_paper = Paper(
                                title=paper.get('title', 'Untitled'),
                                abstract=paper.get('abstract', ''),
                                source=paper.get('source', 'api'),
                                source_id=paper.get('arxiv_id') or paper.get('pmid'),
                                year=paper.get('year'),
                                doi=paper.get('doi')
                            )
                            session.add(new_paper)
                            session.flush()
                            
                            for author_data in paper.get('authors', [])[:10]:
                                author_name = author_data.get('name', '')
                                if author_name:
                                    author = session.query(Author).filter_by(name=author_name).first()
                                    if not author:
                                        author = Author(name=author_name)
                                        session.add(author)
                                        session.flush()
                                    new_paper.authors.append(author)
                            
                            if paper.get('abstract'):
                                entities = extract_entities(paper['abstract'])
                                for method_data in entities['methods'][:10]:
                                    method = session.query(Method).filter_by(name=method_data['name']).first()
                                    if not method:
                                        method = Method(name=method_data['name'], category=method_data.get('category'))
                                        session.add(method)
                                        session.flush()
                                    new_paper.methods.append(method)
                            
                            session.commit()
                            session.close()
                            st.session_state.imported_papers.add(paper_id)
                            st.rerun()
                        except Exception as e:
                            session.rollback()
                            session.close()
                            st.error(f"Failed to import: {str(e)}")
    
    st.markdown("---")
    st.subheader("Topic Clustering")
    
    session = get_session()
    papers = session.query(Paper).all()
    
    if papers and len(papers) >= 3:
        if st.button("Auto-Cluster Papers by Topic"):
            with st.spinner("Clustering papers..."):
                paper_dicts = [{'id': p.id, 'title': p.title, 'abstract': p.abstract or '', 'content': p.content or ''} for p in papers]
                
                clustering_result = cluster_papers(paper_dicts)
                
                if clustering_result['assignments']:
                    st.success(f"Clustered into {clustering_result['n_clusters']} topics (Quality: {clustering_result['quality_score']:.2f})")
                    
                    for cluster_id, label in clustering_result['labels'].items():
                        papers_in_cluster = [paper_dicts[i] for i, c in enumerate(clustering_result['assignments']) if c == cluster_id]
                        
                        with st.expander(f"Topic: {label} ({len(papers_in_cluster)} papers)"):
                            keywords = clustering_result['keywords'].get(cluster_id, [])
                            st.write(f"**Keywords:** {', '.join(keywords)}")
                            for p in papers_in_cluster[:5]:
                                st.write(f"- {p['title'][:70]}...")
    elif papers:
        st.info("Need at least 3 papers for topic clustering")
    
    session.close()


def page_knowledge_graph():
    """Interactive Knowledge Graph Exploration"""
    st.markdown(
        hero_banner("Knowledge Graph Explorer", "Explore connections between papers, methods, datasets, and authors"),
        unsafe_allow_html=True
    )
    
    session = get_session()
    
    tab1, tab2, tab3, tab4 = st.tabs(["Full Knowledge Graph", "Single Paper Graph", "Concept Dependency Map", "Co-authorship Network"])
    
    with tab1:
        st.subheader("Research Knowledge Graph")
        
        with st.expander("ℹ️ How to Read This Graph", expanded=False):
            st.markdown("""
            **What does this graph show?**
            
            This interactive graph visualizes the relationships in your research corpus:
            
            - **Green nodes = Papers** - Each paper you've uploaded
            - **Blue nodes = Methods** - Techniques, algorithms, and approaches used in papers
            - **Orange nodes = Datasets** - Data sources referenced in papers  
            - **Purple nodes = Authors** - Researchers who wrote the papers
            
            **How to interpret:**
            - **Lines (edges)** connect related items (e.g., a paper to its methods)
            - **Larger nodes** have more connections (more influential)
            - **Hover** over any node to see details
            - **Zoom & pan** to explore different areas
            
            **Note:** Only connected nodes are shown. Isolated items without relationships are hidden for clarity.
            """)
        
        papers = session.query(Paper).all()
        methods = session.query(Method).all()
        datasets = session.query(Dataset).all()
        authors = session.query(Author).all()
        
        if papers:
            col_opts1, col_opts2 = st.columns([1, 2])
            with col_opts1:
                show_labels = st.checkbox("Show labels on nodes", value=False, key="kg_show_labels")
            
            paper_dicts = [{'id': p.id, 'title': p.title, 'year': p.year, 
                          'methods': [{'id': m.id, 'name': m.name} for m in p.methods],
                          'datasets': [{'id': d.id, 'name': d.name} for d in p.datasets],
                          'authors': [{'id': a.id, 'name': a.name} for a in p.authors]} 
                         for p in papers]
            method_dicts = [{'id': m.id, 'name': m.name, 'category': m.category, 'usage_count': m.usage_count} for m in methods]
            dataset_dicts = [{'id': d.id, 'name': d.name, 'domain': d.domain, 'usage_count': d.usage_count} for d in datasets]
            author_dicts = [{'id': a.id, 'name': a.name, 'papers': [{'id': p.id} for p in a.papers]} for a in authors]
            
            G = build_knowledge_graph(paper_dicts, method_dicts, dataset_dicts, author_dicts)
            
            connected_count = sum(1 for n in G.nodes() if G.degree(n) > 0)
            total_count = G.number_of_nodes()
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                fig = create_plotly_graph(G, "Research Knowledge Graph", show_labels=show_labels)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### Graph Statistics")
                metrics = calculate_graph_metrics(G)
                st.metric("Connected Nodes", connected_count, help="Nodes with at least one connection")
                st.metric("Edges", metrics['num_edges'], help="Total connections between nodes")
                st.metric("Density", f"{metrics['density']:.4f}", help="How interconnected the graph is (0-1)")
                
                if total_count > connected_count:
                    st.caption(f"*{total_count - connected_count} isolated nodes hidden*")
                
                st.markdown("---")
                st.markdown("### Quick Insights")
                
                paper_count = sum(1 for n in G.nodes() if G.nodes[n].get('type') == 'paper' and G.degree(n) > 0)
                method_count = sum(1 for n in G.nodes() if G.nodes[n].get('type') == 'method' and G.degree(n) > 0)
                dataset_count = sum(1 for n in G.nodes() if G.nodes[n].get('type') == 'dataset' and G.degree(n) > 0)
                author_count = sum(1 for n in G.nodes() if G.nodes[n].get('type') == 'author' and G.degree(n) > 0)
                
                st.write(f"📄 **{paper_count}** papers")
                st.write(f"🔧 **{method_count}** methods")
                st.write(f"📊 **{dataset_count}** datasets")
                st.write(f"👤 **{author_count}** authors")
        else:
            st.info("Upload papers to build the knowledge graph")
    
    with tab2:
        st.subheader("Single Paper Knowledge Graph")
        st.markdown("*View the knowledge graph for a specific paper*")
        
        papers = session.query(Paper).all()
        
        if papers:
            paper_options = {f"{p.title[:60]}..." if len(p.title) > 60 else p.title: p.id for p in papers}
            selected_paper_title = st.selectbox(
                "Select a paper to visualize",
                options=list(paper_options.keys()),
                key="single_paper_graph_select"
            )
            
            if selected_paper_title:
                selected_paper_id = paper_options[selected_paper_title]
                selected_paper = session.query(Paper).filter_by(id=selected_paper_id).first()
                
                if selected_paper:
                    paper_dict = {
                        'id': selected_paper.id,
                        'title': selected_paper.title,
                        'year': selected_paper.year,
                        'methods': [{'id': m.id, 'name': m.name} for m in selected_paper.methods],
                        'datasets': [{'id': d.id, 'name': d.name} for d in selected_paper.datasets],
                        'authors': [{'id': a.id, 'name': a.name} for a in selected_paper.authors]
                    }
                    
                    method_dicts = [{'id': m.id, 'name': m.name, 'category': m.category, 'usage_count': 1} 
                                   for m in selected_paper.methods]
                    dataset_dicts = [{'id': d.id, 'name': d.name, 'domain': d.domain, 'usage_count': 1} 
                                    for d in selected_paper.datasets]
                    author_dicts = [{'id': a.id, 'name': a.name, 'papers': [{'id': selected_paper.id}]} 
                                   for a in selected_paper.authors]
                    
                    G = build_knowledge_graph([paper_dict], method_dicts, dataset_dicts, author_dicts)
                    
                    show_labels_single = st.checkbox("Show labels on nodes", value=True, key="single_paper_show_labels")
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        fig = create_plotly_graph(G, f"Knowledge Graph: {selected_paper.title[:40]}...", show_labels=show_labels_single)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.markdown("### Paper Details")
                        st.write(f"**Title:** {selected_paper.title}")
                        st.write(f"**Year:** {selected_paper.year or 'Unknown'}")
                        
                        st.markdown("### Connections")
                        st.metric("Methods", len(selected_paper.methods))
                        st.metric("Datasets", len(selected_paper.datasets))
                        st.metric("Authors", len(selected_paper.authors))
                        
                        st.markdown("### Legend")
                        st.markdown("- :green[●] Paper")
                        st.markdown("- :blue[●] Methods")
                        st.markdown("- :orange[●] Datasets")
                        st.markdown("- :violet[●] Authors")
                    
                    st.markdown("---")
                    
                    col_m, col_d, col_a = st.columns(3)
                    
                    with col_m:
                        st.markdown("**Methods Used:**")
                        if selected_paper.methods:
                            for m in selected_paper.methods:
                                st.write(f"- `{m.name}`")
                        else:
                            st.write("*No methods extracted*")
                    
                    with col_d:
                        st.markdown("**Datasets Used:**")
                        if selected_paper.datasets:
                            for d in selected_paper.datasets:
                                st.write(f"- `{d.name}`")
                        else:
                            st.write("*No datasets extracted*")
                    
                    with col_a:
                        st.markdown("**Authors:**")
                        if selected_paper.authors:
                            for a in selected_paper.authors[:10]:
                                st.write(f"- {a.name}")
                            if len(selected_paper.authors) > 10:
                                st.write(f"*...and {len(selected_paper.authors) - 10} more*")
                        else:
                            st.write("*No authors extracted*")
        else:
            st.info("Upload papers to view individual knowledge graphs")
    
    with tab3:
        st.subheader("Concept Dependency Map")
        st.markdown("*Understanding prerequisite relationships between methods*")
        
        methods = session.query(Method).all()
        
        if methods:
            prerequisites = build_method_prerequisites()
            method_dicts = [{'name': m.name, 'category': m.category, 'usage_count': m.usage_count} for m in methods]
            
            G = build_method_dag(method_dicts, prerequisites)
            
            if G.number_of_nodes() > 0:
                fig = create_method_dag_visualization(G, "Method Prerequisites")
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("### Learning Pathway")
                st.info("""
                **Example learning sequence:**
                1. Neural Network → RNN → LSTM → Attention Mechanism → Transformer
                2. Transformer → BERT, GPT → GPT-2 → GPT-3 → GPT-4
                3. Generative Models → GAN → Diffusion Model → Stable Diffusion
                """)
            else:
                st.info("Add more papers to build the concept dependency map")
        else:
            st.info("Upload papers to see concept dependencies")
    
    with tab4:
        st.subheader("Co-authorship Network")
        
        authors = session.query(Author).all()
        papers = session.query(Paper).all()
        
        if authors and len(authors) > 1:
            paper_dicts = [{'id': p.id, 'authors': [{'id': a.id, 'name': a.name} for a in p.authors]} for p in papers]
            author_dicts = [{'id': a.id, 'name': a.name, 'papers': [{'id': p.id} for p in a.papers]} for a in authors]
            
            G = build_coauthorship_network(author_dicts, paper_dicts)
            
            if G.number_of_edges() > 0:
                pos = nx.spring_layout(G, k=2, iterations=50)
                
                edge_x, edge_y = [], []
                for edge in G.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                
                edge_trace = go.Scatter(x=edge_x, y=edge_y, mode='lines',
                                       line=dict(width=0.5, color='rgba(168,179,199,0.35)'), hoverinfo='none')

                node_x, node_y, node_text = [], [], []
                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    node_text.append(G.nodes[node].get('name', str(node)))

                node_trace = go.Scatter(
                    x=node_x, y=node_y, mode='markers+text',
                    marker=dict(size=15, color=NODE_TYPE_COLORS['author'], line=dict(width=1.5, color='#0d1220')),
                    text=node_text, textposition='top center',
                    textfont=dict(size=8, color='#a8b3c7')
                )
                
                fig = go.Figure(data=[edge_trace, node_trace])
                fig.update_layout(
                    title="Co-authorship Network",
                    showlegend=False, hovermode='closest',
                    margin=dict(b=20, l=5, r=5, t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                opportunities = find_collaboration_opportunities(G)
                if opportunities:
                    st.markdown("### Potential Collaborations")
                    for opp in opportunities[:5]:
                        st.write(f"- {opp['node1_name']} & {opp['node2_name']} ({opp['common_neighbors']} common collaborators)")
            else:
                st.info("Not enough co-authored papers to build the network")
        else:
            st.info("Upload papers with multiple authors to see the collaboration network")
    
    session.close()


def page_qa():
    """Evidence-Backed Q&A with RAG"""
    st.markdown(
        hero_banner("Research Q&A", "Ask questions and get evidence-backed answers with source citations"),
        unsafe_allow_html=True
    )
    
    if not openai_available():
        st.warning("OpenAI API key not configured. Please add your API key to use this feature.")
        st.info("Add OPENAI_API_KEY to your environment variables to enable AI-powered Q&A.")
        return
    
    session = get_session()
    
    paper_options = {p.title[:80]: p.id for p in session.query(Paper).all()}
    
    if paper_options:
        selected_paper = st.selectbox("Select a paper (or ask across all papers)", 
                                      ["All Papers"] + list(paper_options.keys()))
        
        question = st.text_area("Ask a research question:", 
                               placeholder="What methods were used for data augmentation?")
        
        if st.button("Get Answer", type="primary") and question:
            with st.spinner("Searching for relevant context and generating answer..."):
                if selected_paper == "All Papers":
                    chunks = session.query(PaperChunk).all()
                else:
                    paper_id = paper_options[selected_paper]
                    chunks = session.query(PaperChunk).filter_by(paper_id=paper_id).all()
                
                if chunks:
                    search_results = st.session_state.search_index.search_chunks(question, top_k=5)
                    
                    if not search_results:
                        search_results = [{'content': c.content, 'paper_id': c.paper_id, 
                                         'section': c.section} for c in chunks[:5]]
                    
                    for result in search_results:
                        if 'paper_id' in result:
                            paper = session.query(Paper).get(result['paper_id'])
                            if paper:
                                result['paper_title'] = paper.title
                    
                    response = answer_question(question, search_results)
                    
                    st.markdown("### Answer")
                    st.write(response['answer'])
                    
                    if response['sources']:
                        st.markdown("### Sources")
                        for source in response['sources']:
                            with st.expander(f"Source {source['index']}: {source['paper_title'][:50]}..."):
                                st.write(f"**Section:** {source['section']}")
                                st.write(source['content'])
                    
                    saved_query = SavedQuery(
                        query=question,
                        response=response['answer'],
                        sources=[{'title': s['paper_title'], 'section': s['section']} for s in response['sources']]
                    )
                    session.add(saved_query)
                    session.commit()
                else:
                    st.warning("No paper content available. Please upload papers first.")
        
        st.markdown("---")
        st.subheader("Previous Questions")
        
        saved_queries = session.query(SavedQuery).order_by(SavedQuery.created_at.desc()).limit(5).all()
        for q in saved_queries:
            with st.expander(q.query[:100] + "..." if len(q.query) > 100 else q.query):
                st.write(q.response)
    else:
        st.info("Upload papers to start asking questions")
    
    session.close()


def page_summaries():
    """Multi-Audience Summaries"""
    st.markdown(
        hero_banner("Multi-Audience Summaries", "Generate tailored summaries for different audiences"),
        unsafe_allow_html=True
    )
    
    if not openai_available():
        st.warning("OpenAI API key not configured. Please add your API key to use this feature.")
        return
    
    session = get_session()
    papers = session.query(Paper).all()
    
    if papers:
        paper_options = {p.title[:80]: p.id for p in papers}
        selected_paper_title = st.selectbox("Select a paper", list(paper_options.keys()))
        
        paper_id = paper_options[selected_paper_title]
        paper = session.query(Paper).get(paper_id)
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### Expert Summary")
            st.caption("Technical details for researchers")
            if st.button("Generate Expert Summary", key="expert"):
                with st.spinner("Generating expert summary..."):
                    summary = generate_summary(paper.content or paper.abstract, "expert")
                    st.write(summary)
        
        with col2:
            st.markdown("### Student Summary")
            st.caption("Simple explanations with analogies")
            if st.button("Generate Student Summary", key="student"):
                with st.spinner("Generating student summary..."):
                    summary = generate_summary(paper.content or paper.abstract, "student")
                    st.write(summary)
        
        with col3:
            st.markdown("### Policymaker Summary")
            st.caption("Applications, risks, and implications")
            if st.button("Generate Policymaker Summary", key="policymaker"):
                with st.spinner("Generating policymaker summary..."):
                    summary = generate_summary(paper.content or paper.abstract, "policymaker")
                    st.write(summary)
        
        st.markdown("---")
        
        st.subheader("Policy Brief Generator")
        
        if st.button("Generate Full Policy Brief", type="primary"):
            with st.spinner("Generating comprehensive policy brief..."):
                brief = generate_policy_brief(paper.content or paper.abstract, paper.title)
                st.markdown(brief)
                
                st.download_button(
                    "Download Policy Brief",
                    brief,
                    file_name=f"policy_brief_{paper.title[:30].replace(' ', '_')}.md",
                    mime="text/markdown"
                )
        
        st.markdown("---")
        
        st.subheader("Cross-Domain Analogies")
        
        if paper.methods:
            method_names = [m.name for m in paper.methods]
            selected_method = st.selectbox("Select a concept to explain", method_names)
            
            if st.button("Generate Analogy"):
                with st.spinner("Creating intuitive analogy..."):
                    analogy = generate_analogy(selected_method, paper.abstract or "")
                    st.info(analogy)
    else:
        st.info("Upload papers to generate summaries")
    
    session.close()


def page_analytics():
    """Analytics Dashboard with 8+ SQL Reports"""
    st.markdown(
        hero_banner("Analytics Dashboard", "Research intelligence with advanced SQL analytics"),
        unsafe_allow_html=True
    )
    
    session = get_session()
    
    stats = get_summary_statistics(session)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Papers", stats['total_papers'])
    col2.metric("Authors", stats['total_authors'])
    col3.metric("Methods", stats['total_methods'])
    col4.metric("Datasets", stats['total_datasets'])
    col5.metric("Institutions", stats['total_institutions'])
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Trends & Growth", "Authors & Collaboration", "Methods & Datasets", "Advanced Reports"])
    
    with tab1:
        st.subheader("Research Trends Over Time")
        
        col1, col2 = st.columns(2)
        
        with col1:
            yearly_stats = get_yearly_publication_stats(session)
            if yearly_stats:
                df = pd.DataFrame(yearly_stats)
                df['year'] = df['year'].astype(int)
                fig = px.bar(df, x='year', y='count', title="Papers by Year")
                fig.update_xaxes(tickmode='linear', tick0=df['year'].min(), dtick=1, tickformat='d')
                fig.update_yaxes(tickmode='linear', tick0=0, dtick=1)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Upload papers to see publication trends")
        
        with col2:
            growth_data = get_research_growth_by_field(session)
            if growth_data:
                df = pd.DataFrame(growth_data)
                df['year'] = df['year'].astype(int)
                fig = px.line(df, x='year', y='count', color='category', 
                            title="Research Growth by Field", markers=True)
                fig.update_xaxes(tickmode='linear', tick0=df['year'].min(), dtick=1, tickformat='d')
                fig.update_yaxes(tickmode='linear', tick0=0, dtick=max(1, df['count'].max() // 5))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Upload papers to see growth trends")
        
        trending = get_trending_topics_over_time(session)
        if trending:
            st.subheader("Trending Topics Over Time")
            df = pd.DataFrame(trending[:20])
            st.dataframe(df, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Trend Forecasting")
        
        if trending:
            trends = analyze_method_trends(trending)
            
            if trends:
                summary = generate_forecast_summary(trends)
                st.markdown(summary)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Emerging Methods")
                    emerging_methods = identify_emerging_methods(trends)
                    if emerging_methods:
                        for m in emerging_methods[:5]:
                            st.success(f"**{m['method']}** - {m['recent_growth']:.1f}% growth")
                    else:
                        st.info("No strongly emerging methods detected")
                
                with col2:
                    st.markdown("### Declining Methods")
                    declining_methods = identify_declining_methods(trends)
                    if declining_methods:
                        for m in declining_methods[:5]:
                            st.warning(f"**{m['method']}** - peaked in {m['peak_year']}")
                    else:
                        st.info("No strongly declining methods detected")
                
                st.markdown("### Method Trajectory Predictions")
                method_names = list(trends.keys())[:5]
                if method_names:
                    timeline_data = create_timeline_data(trends, method_names)
                    
                    chart_data = []
                    for method, series in timeline_data['series'].items():
                        for year, count in series.get('historical', {}).items():
                            chart_data.append({'Method': method, 'Year': year, 'Count': count, 'Type': 'Historical'})
                        for year, count in series.get('predicted', {}).items():
                            chart_data.append({'Method': method, 'Year': year, 'Count': count, 'Type': 'Predicted'})
                    
                    if chart_data:
                        chart_df = pd.DataFrame(chart_data)
                        fig = px.line(chart_df, x='Year', y='Count', color='Method', 
                                    line_dash='Type', title="Method Popularity Forecast")
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Upload papers with year data to see trend forecasting")
    
    with tab2:
        st.subheader("Author Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            top_authors = get_top_authors_by_publication(session)
            if top_authors:
                st.markdown("### Top Authors by Publication Count")
                df = pd.DataFrame(top_authors)
                fig = px.bar(df.head(10), x='name', y='paper_count', 
                           title="Top 10 Authors")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            coauthor_pairs = get_top_coauthorship_pairs(session)
            if coauthor_pairs:
                st.markdown("### Top Co-authorship Pairs")
                df = pd.DataFrame(coauthor_pairs)
                st.dataframe(df, use_container_width=True)
        
        network_stats = get_collaboration_network_density(session)
        st.markdown("### Collaboration Network Statistics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Authors", network_stats['total_authors'])
        col2.metric("Unique Collaborations", network_stats['unique_collaborations'])
        col3.metric("Network Density", f"{network_stats['network_density']:.4f}")
        col4.metric("Avg Collaborators", network_stats['avg_collaborators_per_author'])
    
    with tab3:
        st.subheader("Methods & Datasets Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            method_dist = get_method_category_distribution(session)
            if method_dist:
                st.markdown("### Method Distribution by Category")
                df = pd.DataFrame(method_dist)
                fig = px.pie(df, values='method_count', names='category',
                           title="Methods by Category")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            top_datasets = get_most_used_datasets(session)
            if top_datasets:
                st.markdown("### Most Used Datasets")
                df = pd.DataFrame(top_datasets)
                fig = px.bar(df.head(10), x='name', y='usage_count',
                           title="Top 10 Datasets")
                st.plotly_chart(fig, use_container_width=True)
        
        cooccurrence = get_dataset_method_cooccurrence(session)
        if cooccurrence:
            st.markdown("### Dataset-Method Co-occurrence")
            df = pd.DataFrame(cooccurrence)
            
            pivot = df.pivot_table(index='dataset', columns='method', values='count', fill_value=0)
            if not pivot.empty and pivot.shape[0] > 0 and pivot.shape[1] > 0:
                fig = px.imshow(pivot.head(10).T.head(10), 
                              title="Dataset-Method Heatmap",
                              labels=dict(x="Dataset", y="Method", color="Co-occurrence"))
                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Advanced SQL Reports")
        
        st.markdown("### Report 1: Papers per Institution")
        inst_data = get_papers_per_institution(session)
        if inst_data:
            df = pd.DataFrame(inst_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No institution data available")
        
        st.markdown("### Report 2: Emerging Methods")
        emerging = get_emerging_methods(session)
        if emerging:
            df = pd.DataFrame(emerging)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No emerging methods detected yet")
        
    
    session.close()


def page_learning():
    """Learning Mode with Flashcards and Quizzes"""
    st.markdown(
        hero_banner("Learning Mode", "Interactive learning tools: concept maps, flashcards, and quizzes"),
        unsafe_allow_html=True
    )
    
    if not openai_available():
        st.warning("OpenAI API key not configured. Please add your API key to use this feature.")
        return
    
    session = get_session()
    papers = session.query(Paper).all()
    
    if papers:
        paper_options = {p.title[:80]: p.id for p in papers}
        selected_paper_title = st.selectbox("Select a paper to study", list(paper_options.keys()))
        
        paper_id = paper_options[selected_paper_title]
        paper = session.query(Paper).get(paper_id)
        
        tab1, tab2, tab3, tab4 = st.tabs(["Key Insights", "Flashcards", "Quiz", "Study Roadmap"])
        
        with tab1:
            st.subheader("Key Insights")
            
            if st.button("Extract Key Insights", type="primary"):
                with st.spinner("Analyzing paper for key insights..."):
                    insights = extract_key_insights(paper.content or paper.abstract)
                    
                    for i, insight in enumerate(insights, 1):
                        st.success(f"**{i}.** {insight}")
        
        with tab2:
            st.subheader("Flashcards")
            
            existing_flashcards = session.query(Flashcard).filter_by(paper_id=paper_id).all()
            
            if existing_flashcards:
                st.write(f"You have {len(existing_flashcards)} flashcards for this paper.")
                
                if 'flashcard_index' not in st.session_state:
                    st.session_state.flashcard_index = 0
                
                if st.session_state.flashcard_index < len(existing_flashcards):
                    card = existing_flashcards[st.session_state.flashcard_index]
                    
                    st.markdown(f"**Card {st.session_state.flashcard_index + 1} of {len(existing_flashcards)}**")
                    
                    with st.container():
                        st.markdown(f"### Question")
                        st.write(card.question)
                        
                        if st.button("Show Answer"):
                            st.markdown("### Answer")
                            st.write(card.answer)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Previous") and st.session_state.flashcard_index > 0:
                            st.session_state.flashcard_index -= 1
                            st.rerun()
                    with col2:
                        st.write(f"{st.session_state.flashcard_index + 1} / {len(existing_flashcards)}")
                    with col3:
                        if st.button("Next") and st.session_state.flashcard_index < len(existing_flashcards) - 1:
                            st.session_state.flashcard_index += 1
                            st.rerun()
            
            num_cards = st.slider("Number of new flashcards to generate", 3, 10, 5)
            
            if st.button("Generate New Flashcards"):
                with st.spinner("Generating flashcards..."):
                    flashcards = generate_flashcards(paper.content or paper.abstract, num_cards)
                    
                    for card_data in flashcards:
                        flashcard = Flashcard(
                            paper_id=paper_id,
                            question=card_data.get('question', ''),
                            answer=card_data.get('answer', ''),
                            difficulty=card_data.get('difficulty', 'medium')
                        )
                        session.add(flashcard)
                    
                    session.commit()
                    st.success(f"Generated {len(flashcards)} flashcards!")
                    st.rerun()
        
        with tab3:
            st.subheader("Quiz")
            
            num_questions = st.slider("Number of quiz questions", 3, 10, 5)
            
            if st.button("Start Quiz"):
                with st.spinner("Generating quiz questions..."):
                    questions = generate_quiz(paper.content or paper.abstract, num_questions)
                    
                    if questions:
                        st.session_state.quiz_questions = questions
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
            
            if 'quiz_questions' in st.session_state and st.session_state.quiz_questions:
                questions = st.session_state.quiz_questions
                
                with st.form("quiz_form"):
                    for i, q in enumerate(questions):
                        st.markdown(f"**Q{i+1}: {q['question']}**")
                        
                        answer = st.radio(
                            f"Select answer for Q{i+1}:",
                            q['options'],
                            key=f"q_{i}"
                        )
                        st.session_state.quiz_answers[i] = answer
                        st.markdown("---")
                    
                    submitted = st.form_submit_button("Submit Quiz")
                    
                    if submitted:
                        correct = 0
                        for i, q in enumerate(questions):
                            user_answer = st.session_state.quiz_answers.get(i, "")
                            if user_answer and user_answer.startswith(q['correct_answer']):
                                correct += 1
                        
                        score = (correct / len(questions)) * 100
                        st.session_state.quiz_score = score
                        st.session_state.quiz_submitted = True
                
                if st.session_state.get('quiz_submitted'):
                    score = st.session_state.quiz_score
                    if score >= 80:
                        st.success(f"Great job! You scored {score:.0f}%")
                    elif score >= 60:
                        st.warning(f"Good effort! You scored {score:.0f}%")
                    else:
                        st.error(f"Keep studying! You scored {score:.0f}%")
        
        with tab4:
            st.subheader("Personalized Study Roadmap")
            
            st.markdown("""
            Based on the methods used in this paper, here's a suggested learning path:
            """)
            
            if paper.methods:
                prerequisites = build_method_prerequisites()
                
                for method in paper.methods[:5]:
                    prereqs = prerequisites.get(method.name, [])
                    if prereqs:
                        st.markdown(f"**To understand {method.name}:**")
                        for i, prereq in enumerate(prereqs, 1):
                            st.markdown(f"  {i}. First learn: {prereq}")
                        st.markdown("")
                    else:
                        st.markdown(f"**{method.name}** - Foundational concept")
            else:
                st.info("Methods will appear here after paper processing")
    else:
        st.info("Upload papers to start learning")
    
    session.close()


def page_workspace():
    """Personal Research Workspace"""
    st.markdown(
        hero_banner("Research Workspace", "Organize your research: saved papers, notes, and reading lists"),
        unsafe_allow_html=True
    )
    
    session = get_session()
    
    tab1, tab2, tab3 = st.tabs(["Reading List", "Notes", "Export"])
    
    with tab1:
        st.subheader("Reading List")
        
        papers = session.query(Paper).all()
        reading_list = session.query(ReadingList).all()
        reading_paper_ids = {r.paper_id for r in reading_list}
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Add Papers to Reading List")
            
            available_papers = [p for p in papers if p.id not in reading_paper_ids]
            
            if available_papers:
                paper_to_add = st.selectbox(
                    "Select a paper to add",
                    options=[(p.id, p.title[:70]) for p in available_papers],
                    format_func=lambda x: x[1]
                )
                
                priority = st.slider("Priority (1=highest)", 1, 5, 3)
                
                if st.button("Add to Reading List"):
                    new_item = ReadingList(paper_id=paper_to_add[0], priority=priority)
                    session.add(new_item)
                    session.commit()
                    st.success("Added to reading list!")
                    st.rerun()
        
        with col2:
            st.markdown("### Your Reading List")
            
            reading_items = session.query(ReadingList).order_by(ReadingList.priority).all()
            
            for item in reading_items:
                paper = session.query(Paper).get(item.paper_id)
                if paper:
                    status_emoji = {"unread": "📚", "reading": "📖", "completed": "✅"}
                    
                    with st.expander(f"{status_emoji.get(item.status, '📄')} {paper.title[:40]}..."):
                        st.write(f"**Priority:** {item.priority}")
                        st.write(f"**Status:** {item.status}")
                        
                        new_status = st.selectbox(
                            "Update status",
                            ["unread", "reading", "completed"],
                            index=["unread", "reading", "completed"].index(item.status),
                            key=f"status_{item.id}"
                        )
                        
                        if new_status != item.status:
                            item.status = new_status
                            session.commit()
                            st.rerun()
                        
                        if st.button("Remove", key=f"remove_{item.id}"):
                            session.delete(item)
                            session.commit()
                            st.rerun()
    
    with tab2:
        st.subheader("Research Notes")
        
        if papers:
            paper_options = {p.title[:70]: p.id for p in papers}
            selected_paper = st.selectbox("Select paper for notes", list(paper_options.keys()))
            paper_id = paper_options[selected_paper]
            
            existing_notes = session.query(Note).filter_by(paper_id=paper_id).all()
            
            st.markdown("### Your Notes")
            for note in existing_notes:
                with st.expander(f"Note from {note.created_at.strftime('%Y-%m-%d %H:%M')}"):
                    st.write(note.content)
                    if st.button("Delete", key=f"del_note_{note.id}"):
                        session.delete(note)
                        session.commit()
                        st.rerun()
            
            st.markdown("### Add New Note")
            new_note = st.text_area("Write your note")
            
            if st.button("Save Note") and new_note:
                note = Note(paper_id=paper_id, content=new_note)
                session.add(note)
                session.commit()
                st.success("Note saved!")
                st.rerun()
        else:
            st.info("Upload papers to add notes")
    
    with tab3:
        st.subheader("Export Literature Review")
        
        papers = session.query(Paper).all()
        
        if papers:
            st.markdown("### Select Papers for Export")
            
            selected_papers = st.multiselect(
                "Select papers to include",
                options=[(p.id, p.title[:70]) for p in papers],
                format_func=lambda x: x[1]
            )
            
            export_format = st.selectbox(
                "Export Format",
                ["Markdown", "LaTeX", "BibTeX", "Plain Text", "CSV"]
            )
            
            include_notes = st.checkbox("Include notes", value=True)
            
            if st.button("Generate Export", type="primary") and selected_papers:
                paper_dicts = []
                notes_dict = {}
                
                for paper_id, _ in selected_papers:
                    paper = session.query(Paper).get(paper_id)
                    if paper:
                        paper_dict = {
                            'id': paper.id,
                            'title': paper.title,
                            'abstract': paper.abstract,
                            'year': paper.year,
                            'doi': paper.doi,
                            'venue': paper.venue,
                            'source': paper.source,
                            'authors': [{'name': a.name} for a in paper.authors],
                            'methods': [{'name': m.name} for m in paper.methods],
                            'datasets': [{'name': d.name} for d in paper.datasets]
                        }
                        paper_dicts.append(paper_dict)
                        
                        if include_notes:
                            paper_notes = session.query(Note).filter_by(paper_id=paper_id).all()
                            notes_dict[paper_id] = [n.content for n in paper_notes]
                
                if export_format == "Markdown":
                    content = generate_markdown_review(paper_dicts, notes_dict)
                    st.markdown(content)
                    st.download_button(
                        "Download Markdown",
                        content,
                        file_name="literature_review.md",
                        mime="text/markdown"
                    )
                
                elif export_format == "LaTeX":
                    content = generate_latex_review(paper_dicts, notes_dict)
                    st.code(content, language="latex")
                    st.download_button(
                        "Download LaTeX",
                        content,
                        file_name="literature_review.tex",
                        mime="text/x-tex"
                    )
                
                elif export_format == "BibTeX":
                    content = generate_bibtex(paper_dicts)
                    st.code(content, language="bibtex")
                    st.download_button(
                        "Download BibTeX",
                        content,
                        file_name="references.bib",
                        mime="text/x-bibtex"
                    )
                
                elif export_format == "Plain Text":
                    content = generate_plain_text_review(paper_dicts, notes_dict)
                    st.text(content)
                    st.download_button(
                        "Download Text",
                        content,
                        file_name="literature_review.txt",
                        mime="text/plain"
                    )
                
                elif export_format == "CSV":
                    content = generate_csv_export(paper_dicts)
                    st.dataframe(pd.read_csv(pd.io.common.StringIO(content)))
                    st.download_button(
                        "Download CSV",
                        content,
                        file_name="papers_export.csv",
                        mime="text/csv"
                    )
            
            st.markdown("---")
            st.subheader("Export Statistics")
            
            if selected_papers:
                paper_dicts = []
                for paper_id, _ in selected_papers:
                    paper = session.query(Paper).get(paper_id)
                    if paper:
                        paper_dicts.append({
                            'id': paper.id,
                            'title': paper.title,
                            'year': paper.year,
                            'authors': [{'name': a.name} for a in paper.authors],
                            'methods': [{'name': m.name} for m in paper.methods],
                            'datasets': [{'name': d.name} for d in paper.datasets],
                            'source': paper.source
                        })
                
                if paper_dicts:
                    stats = create_export_stats(paper_dicts)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Selected Papers", stats['total_papers'])
                        if stats['year_range']:
                            st.write(f"**Year Range:** {stats['year_range']}")
                        if stats['top_authors']:
                            st.write(f"**Top Authors:** {', '.join(stats['top_authors'][:5])}")
                    
                    with col2:
                        if stats['top_methods']:
                            st.write(f"**Top Methods:** {', '.join(stats['top_methods'][:5])}")
                        if stats['top_datasets']:
                            st.write(f"**Top Datasets:** {', '.join(stats['top_datasets'][:5])}")
        else:
            st.info("Upload papers to export literature reviews")
    
    session.close()


if __name__ == "__main__":
    main()
