import { motion } from "framer-motion";
import { useState } from "react";

export default function SkillGraph() {
  const [hoveredNode, setHoveredNode] = useState(null);

  const nodes = [
    { id: "core", x: 50, y: 50, r: 8, label: "YOU", color: "#F59E0B" },
    { id: "py", x: 20, y: 30, r: 5, label: "Python", color: "#FFFFFF" },
    { id: "js", x: 80, y: 20, r: 5, label: "React", color: "#FFFFFF" },
    { id: "ai", x: 70, y: 80, r: 6, label: "LLMs", color: "#10B981" },
    { id: "fe", x: 30, y: 70, r: 5, label: "FastAPI", color: "#FFFFFF" },
  ];

  const links = [
    { from: "core", to: "py" },
    { from: "core", to: "js" },
    { from: "core", to: "ai" },
    { from: "core", to: "fe" },
    { from: "py", to: "ai" }, 
    { from: "js", to: "fe" }, 
  ];

  return (
    <div className="w-full h-[300px] bg-void relative overflow-hidden rounded-xl border border-border">
      <div className="absolute inset-0 flex items-center justify-center">
        <svg viewBox="0 0 100 100" className="w-full h-full p-8">
          {/* Links */}
          {links.map((link, i) => {
            const start = nodes.find((n) => n.id === link.from);
            const end = nodes.find((n) => n.id === link.to);
            const isConnected = hoveredNode && (link.from === hoveredNode || link.to === hoveredNode);
            
            return (
              <motion.line
                key={i}
                x1={start.x}
                y1={start.y}
                x2={end.x}
                y2={end.y}
                stroke={isConnected ? "#F59E0B" : "#262626"}
                strokeWidth={isConnected ? "1" : "0.5"}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1.5, delay: 0.5 }}
              />
            );
          })}

          {/* Nodes */}
          {nodes.map((node, i) => (
            <motion.g
              key={node.id}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: i * 0.1, type: "spring" }}
              onMouseEnter={() => setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
              style={{ cursor: 'pointer' }}
            >
              {/* Pulse Effect for Core and AI */}
              {(node.id === "core" || node.id === "ai") && (
                <motion.circle
                  cx={node.x}
                  cy={node.y}
                  r={node.r * 2}
                  fill={node.color}
                  initial={{ opacity: 0.2, scale: 1 }}
                  animate={{ opacity: 0, scale: 2 }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              )}
              
              <circle
                cx={node.x}
                cy={node.y}
                r={node.r}
                fill={node.color === "#FFFFFF" ? "#121212" : node.color}
                stroke={node.color}
                strokeWidth={hoveredNode === node.id ? "2" : "1"}
                className="transition-all duration-300"
              />
              <text
                x={node.x}
                y={node.y + node.r + 5}
                fontSize="4"
                fill={hoveredNode === node.id ? "#FFFFFF" : "#A1A1AA"}
                textAnchor="middle"
                className="font-mono uppercase pointer-events-none transition-colors"
              >
                {node.label}
              </text>
            </motion.g>
          ))}
        </svg>
      </div>
      <div className="absolute top-4 left-4 text-xs font-mono text-text-dim">
        SKILL_TOPOLOGY_V2
      </div>
    </div>
  );
}