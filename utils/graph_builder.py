"""
Knowledge Graph builder and visualization for ScholarLens
Creates interactive network visualizations using NetworkX and Plotly
"""

import networkx as nx
import plotly.graph_objects as go
from typing import List, Dict, Tuple, Optional
import json

from utils.theme import NODE_TYPE_COLORS, CATEGORICAL, TEXT_PRIMARY, TEXT_SECONDARY, BG_SURFACE


def build_knowledge_graph(papers: List[Dict], methods: List[Dict], 
                          datasets: List[Dict], authors: List[Dict]) -> nx.Graph:
    """
    Build a knowledge graph from extracted entities
    """
    G = nx.Graph()
    
    for paper in papers:
        G.add_node(
            f"paper_{paper['id']}",
            type='paper',
            label=paper.get('title', 'Unknown')[:50],
            full_title=paper.get('title', 'Unknown'),
            year=paper.get('year'),
            size=20
        )
    
    for method in methods:
        G.add_node(
            f"method_{method['id']}",
            type='method',
            label=method.get('name', 'Unknown'),
            category=method.get('category', 'unknown'),
            usage_count=method.get('usage_count', 0),
            size=15 + min(method.get('usage_count', 0) * 2, 30)
        )
    
    for dataset in datasets:
        G.add_node(
            f"dataset_{dataset['id']}",
            type='dataset',
            label=dataset.get('name', 'Unknown'),
            domain=dataset.get('domain', 'unknown'),
            usage_count=dataset.get('usage_count', 0),
            size=15 + min(dataset.get('usage_count', 0) * 2, 30)
        )
    
    for author in authors:
        G.add_node(
            f"author_{author['id']}",
            type='author',
            label=author.get('name', 'Unknown'),
            paper_count=len(author.get('papers', [])),
            size=12 + min(len(author.get('papers', [])) * 3, 25)
        )
    
    for paper in papers:
        paper_node = f"paper_{paper['id']}"
        
        for method in paper.get('methods', []):
            method_node = f"method_{method['id']}"
            if G.has_node(method_node):
                G.add_edge(paper_node, method_node, type='uses_method', weight=1)
        
        for dataset in paper.get('datasets', []):
            dataset_node = f"dataset_{dataset['id']}"
            if G.has_node(dataset_node):
                G.add_edge(paper_node, dataset_node, type='uses_dataset', weight=1)
        
        for author in paper.get('authors', []):
            author_node = f"author_{author['id']}"
            if G.has_node(author_node):
                G.add_edge(paper_node, author_node, type='authored_by', weight=1)
    
    return G


def build_method_dag(methods: List[Dict], prerequisites: Dict[str, List[str]]) -> nx.DiGraph:
    """
    Build a directed acyclic graph of method prerequisites
    """
    G = nx.DiGraph()
    
    for method in methods:
        G.add_node(
            method['name'],
            category=method.get('category', 'unknown'),
            usage_count=method.get('usage_count', 0)
        )
    
    for method_name, prereqs in prerequisites.items():
        if G.has_node(method_name):
            for prereq in prereqs:
                if G.has_node(prereq):
                    G.add_edge(prereq, method_name)
                else:
                    G.add_node(prereq, category='foundation', usage_count=0)
                    G.add_edge(prereq, method_name)
    
    return G


def create_plotly_graph(G: nx.Graph, title: str = "Knowledge Graph", show_labels: bool = False) -> go.Figure:
    """
    Create an interactive Plotly visualization of a NetworkX graph
    Only shows connected nodes (removes orphans) for cleaner visualization
    """
    connected_nodes = [node for node in G.nodes() if G.degree(node) > 0]
    
    if not connected_nodes:
        fig = go.Figure()
        fig.add_annotation(
            text="No connected nodes to display.<br>Upload papers to build relationships.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color=TEXT_SECONDARY)
        )
        fig.update_layout(
            title=dict(text=title, x=0.5),
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        return fig
    
    H = G.subgraph(connected_nodes).copy()
    
    num_nodes = H.number_of_nodes()
    k_value = max(0.5, 3 / (num_nodes ** 0.5)) if num_nodes > 1 else 1
    iterations = min(100, max(50, num_nodes * 2))
    
    pos = nx.spring_layout(H, k=k_value, iterations=iterations, seed=42)

    node_colors = NODE_TYPE_COLORS

    edge_x = []
    edge_y = []
    for edge in H.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode='lines',
        line=dict(width=1, color='rgba(168,179,199,0.3)'),
        hoverinfo='none',
        showlegend=False
    )
    
    node_traces = {}
    for node_type in node_colors.keys():
        node_traces[node_type] = {
            'x': [], 'y': [], 'text': [], 'hover_text': [], 'size': [], 'customdata': []
        }
    
    for node in H.nodes():
        x, y = pos[node]
        node_data = H.nodes[node]
        node_type = node_data.get('type', 'paper')
        degree = H.degree(node)
        
        if node_type in node_traces:
            node_traces[node_type]['x'].append(x)
            node_traces[node_type]['y'].append(y)
            label = node_data.get('label', node)
            node_traces[node_type]['text'].append(label if show_labels else '')
            node_traces[node_type]['hover_text'].append(f"{label}<br>Type: {node_type}<br>Connections: {degree}")
            base_size = node_data.get('size', 15)
            size = base_size + (degree * 2)
            node_traces[node_type]['size'].append(min(size, 40))
            node_traces[node_type]['customdata'].append(node)
    
    fig = go.Figure()
    
    fig.add_trace(edge_trace)
    
    for node_type, data in node_traces.items():
        if data['x']:
            fig.add_trace(go.Scatter(
                x=data['x'],
                y=data['y'],
                mode='markers+text' if show_labels else 'markers',
                marker=dict(
                    size=data['size'],
                    color=node_colors.get(node_type, '#888'),
                    line=dict(width=2, color='white'),
                    opacity=0.9
                ),
                text=data['text'],
                textposition='top center',
                textfont=dict(size=9, color='white'),
                customdata=data['customdata'],
                name=node_type.capitalize(),
                hovertext=data['hover_text'],
                hoverinfo='text'
            ))
    
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=16)),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(0,0,0,0.3)',
            font=dict(size=11)
        ),
        hovermode='closest',
        dragmode='pan',
        margin=dict(b=20, l=5, r=5, t=60),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, fixedrange=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, fixedrange=False, scaleanchor='x', scaleratio=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=600
    )
    
    fig.update_layout(
        modebar=dict(
            orientation='v',
            bgcolor='rgba(0,0,0,0.5)',
            activecolor=CATEGORICAL[0]
        ),
        modebar_add=['pan2d', 'zoom2d', 'zoomIn2d', 'zoomOut2d', 'resetScale2d']
    )
    
    return fig


def create_method_dag_visualization(G: nx.DiGraph, title: str = "Concept Dependency Map") -> go.Figure:
    """
    Create a hierarchical visualization for method prerequisites
    """
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
    except:
        for layer, nodes in enumerate(nx.topological_generations(G)):
            for i, node in enumerate(nodes):
                pos = getattr(G, '_pos', {})
                pos[node] = (i * 100, layer * 100)
                G._pos = pos
        pos = getattr(G, '_pos', nx.spring_layout(G))
    
    edge_x = []
    edge_y = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='rgba(168,179,199,0.35)'),
        hoverinfo='none',
        mode='lines'
    )
    
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        node_size.append(20 + G.nodes[node].get('usage_count', 0) * 2)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition='top center',
        marker=dict(
            size=node_size,
            color=CATEGORICAL[0],
            line=dict(width=2, color=BG_SURFACE)
        )
    )
    
    fig = go.Figure(data=[edge_trace, node_trace])
    
    fig.update_layout(
        title=dict(text=title, x=0.5),
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=500
    )
    
    return fig


def build_coauthorship_network(authors: List[Dict], papers: List[Dict]) -> nx.Graph:
    """
    Build a co-authorship network
    """
    G = nx.Graph()
    
    for author in authors:
        G.add_node(
            author['id'],
            name=author.get('name', 'Unknown'),
            paper_count=len(author.get('papers', []))
        )
    
    for paper in papers:
        paper_authors = paper.get('authors', [])
        for i, author1 in enumerate(paper_authors):
            for author2 in paper_authors[i+1:]:
                if G.has_node(author1['id']) and G.has_node(author2['id']):
                    if G.has_edge(author1['id'], author2['id']):
                        G[author1['id']][author2['id']]['weight'] += 1
                    else:
                        G.add_edge(author1['id'], author2['id'], weight=1)
    
    return G


def calculate_graph_metrics(G: nx.Graph) -> Dict:
    """
    Calculate various graph metrics
    """
    metrics = {
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'density': nx.density(G) if G.number_of_nodes() > 1 else 0,
    }
    
    if G.number_of_nodes() > 0:
        if nx.is_connected(G):
            metrics['avg_path_length'] = nx.average_shortest_path_length(G)
        else:
            metrics['avg_path_length'] = 0
        
        metrics['clustering_coefficient'] = nx.average_clustering(G)
        
        degree_centrality = nx.degree_centrality(G)
        metrics['top_central_nodes'] = sorted(
            degree_centrality.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
    
    return metrics


def find_collaboration_opportunities(G: nx.Graph, min_common_neighbors: int = 2) -> List[Dict]:
    """
    Find potential collaboration opportunities based on network structure
    """
    opportunities = []
    
    nodes = list(G.nodes())
    for i, node1 in enumerate(nodes):
        for node2 in nodes[i+1:]:
            if not G.has_edge(node1, node2):
                common = len(list(nx.common_neighbors(G, node1, node2)))
                if common >= min_common_neighbors:
                    opportunities.append({
                        'node1': node1,
                        'node2': node2,
                        'common_neighbors': common,
                        'node1_name': G.nodes[node1].get('name', node1),
                        'node2_name': G.nodes[node2].get('name', node2)
                    })
    
    opportunities.sort(key=lambda x: x['common_neighbors'], reverse=True)
    return opportunities[:20]
