import React, { useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import SubmissionForm from './SubmissionForm';
import './App.css';

function App() {
  const [data, setData] = useState({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    fetch('http://localhost:5001/api/procurement_anomalies') // Fetch from Flask backend
      .then(response => {
        if (!response.ok) {
          console.error('Network response was not ok:', response.status);
          return response.text().then(text => {
            console.error('Received non-JSON response:', text);
            throw new Error('Received non-JSON response');
          });
        }
        return response.json();
      })
      .then(data => setData(data))
      .catch(error => console.error('There was a problem with the fetch operation:', error));
  }, []);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>DITP - Public Trust Map</h1>
        <p>Visualizing the network of corruption in Victoria, Texas</p>
      </header>
      <div className="graph-container">
        <ForceGraph2D
          graphData={data}
          nodeLabel="id"
          nodeAutoColorBy="group"
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={1.5}
          onNodeClick={handleNodeClick}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.id;
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px Sans-Serif`;
            const textWidth = ctx.measureText(label).width;
            const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, ...bckgDimensions);

            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';

            // Define colors based on node group
            const nodeColorMap = {
              government: '#FF5733', // Orange-Red
              financial: '#33FF57',    // Green
              unaudited_entity: '#3357FF', // Blue
              le_abuse: '#FF33A1',    // Pink
              victim: '#FFBD33',      // Gold
              obstruction: '#8D33FF', // Purple
              retaliation: '#33FFF6'  // Cyan
            };

            ctx.fillStyle = nodeColorMap[node.group] || '#e0e0e0'; // Default to light grey if group not found
            ctx.fillText(label, node.x, node.y);

            node.__bckgDimensions = bckgDimensions; // save for selection highlighting
          }}
          nodePointerAreaPaint={(node, color, ctx) => {
            ctx.fillStyle = color;
            const bckgDimensions = node.__bckgDimensions;
            bckgDimensions && ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, ...bckgDimensions);
          }}
        />
      </div>
      {selectedNode && (
        <div className="node-details">
          <h2>{selectedNode.id}</h2>
          <p><strong>Group:</strong> {selectedNode.group}</p>
          <p><strong>Details:</strong> {selectedNode.details}</p>
        </div>
      )}
      <SubmissionForm />
    </div>
  );
}

export default App;