<script>
  import { onMount, onDestroy } from "svelte";

  export let width = 800;
  export let height = 600;
  export let className = "";
  export let yesVotes = 0;
  export let noVotes = 0;

  let canvasElement;
  let animationFrame = null;
  let nodes = [];
  let links = [];
  let lastYesVotes = -1;
  let lastNoVotes = -1;
  let context = null;

  // Reactive statement to regenerate nodes when votes change
  $: if ((yesVotes !== lastYesVotes || noVotes !== lastNoVotes) && canvasElement && context) {
    lastYesVotes = yesVotes;
    lastNoVotes = noVotes;
    regenerateNodes();
  }

  function regenerateNodes() {
    // Generate nodes based on votes
    nodes = [];
    let nodeId = 0;

    // Green nodes for yes votes - start slightly closer to center (15% bias)
    for (let i = 0; i < yesVotes; i++) {
      const centerBias = 0.85; // 85% of screen size (15% closer to center)
      const offsetX = (Math.random() - 0.5) * width * centerBias;
      const offsetY = (Math.random() - 0.5) * height * centerBias;
      
      nodes.push({
        id: `yes-node-${nodeId++}`,
        x: width / 2 + offsetX,
        y: height / 2 + offsetY,
        color: "#19c37a", // Green for yes
        vx: (Math.random() - 0.5) * 0.7,
        vy: (Math.random() - 0.5) * 0.7,
        targetVx: (Math.random() - 0.5) * 0.14,
        targetVy: (Math.random() - 0.5) * 0.14,
      });
    }

    // Red nodes for no votes - start slightly closer to center (15% bias)
    for (let i = 0; i < noVotes; i++) {
      const centerBias = 0.85; // 85% of screen size (15% closer to center)
      const offsetX = (Math.random() - 0.5) * width * centerBias;
      const offsetY = (Math.random() - 0.5) * height * centerBias;
      
      nodes.push({
        id: `no-node-${nodeId++}`,
        x: width / 2 + offsetX,
        y: height / 2 + offsetY,
        color: "#ef4444", // Red for no
        vx: (Math.random() - 0.5) * 0.7,
        vy: (Math.random() - 0.5) * 0.7,
        targetVx: (Math.random() - 0.5) * 0.14,
        targetVy: (Math.random() - 0.5) * 0.14,
      });
    }

    // Generate links between nodes
    links = [];
    for (let i = 0; i < nodes.length - 1; i++) {
      if (Math.random() > 0.85) {
        links.push({
          source: nodes[i],
          target: nodes[i + 1],
          dashed: Math.random() > 0.5,
        });
      }
    }
  }

  onMount(() => {
    if (!canvasElement) return;

    const canvas = canvasElement;
    context = canvas.getContext("2d");
    if (!context) return;

    // Set up canvas
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    context.scale(dpr, dpr);

    // Initial node generation
    regenerateNodes();

    const render = () => {
      // Clear canvas
      context.clearRect(0, 0, width, height);

      // Update node positions with smooth floating motion
      const centerX = width / 2;
      const centerY = height / 2;
      
      nodes.forEach((node) => {
        // Smoothly interpolate towards target velocity for smoother motion
        if (node.targetVx !== undefined && node.targetVy !== undefined) {
          // Slower interpolation for smoother movement
          node.vx += (node.targetVx - node.vx) * 0.03; // Slower interpolation
          node.vy += (node.targetVy - node.vy) * 0.03;
          
          // Less frequently update target velocity to reduce shakiness
          if (Math.random() < 0.02) {
            node.targetVx = (Math.random() - 0.5) * 0.12;
            node.targetVy = (Math.random() - 0.5) * 0.12;
          }
        } else {
          // Fallback for nodes without target velocity
          node.vx = (node.vx || 0) * 0.995 + (Math.random() - 0.5) * 0.04;
          node.vy = (node.vy || 0) * 0.995 + (Math.random() - 0.5) * 0.04;
        }
        
        // Gentle attraction towards center to group them 15% closer (reduced for larger movement)
        const dx = centerX - node.x;
        const dy = centerY - node.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        if (distance > 0) {
          const attractionStrength = 0.0003; // Reduced pull to allow larger movement radius
          node.vx += (dx / distance) * attractionStrength;
          node.vy += (dy / distance) * attractionStrength;
        }

        // Update position
        node.x += node.vx;
        node.y += node.vy;

        // Boundary collision with gentle bounce (allow movement across full screen)
        const margin = 20; // Small margin to keep nodes visible
        if (node.x < margin) {
          node.x = margin;
          node.vx *= -0.8;
          node.targetVx = Math.abs(node.targetVx || 0.3);
        }
        if (node.x > width - margin) {
          node.x = width - margin;
          node.vx *= -0.8;
          node.targetVx = -Math.abs(node.targetVx || 0.3);
        }
        if (node.y < margin) {
          node.y = margin;
          node.vy *= -0.8;
          node.targetVy = Math.abs(node.targetVy || 0.3);
        }
        if (node.y > height - margin) {
          node.y = height - margin;
          node.vy *= -0.8;
          node.targetVy = -Math.abs(node.targetVy || 0.3);
        }
      });

      // Draw links
      links.forEach((link) => {
        context.beginPath();
        context.moveTo(link.source.x, link.source.y);
        context.lineTo(link.target.x, link.target.y);
        context.strokeStyle = "#999";
        context.lineWidth = 2;
        context.globalAlpha = 0.3;
        if (link.dashed) {
          context.setLineDash([8, 4]);
        } else {
          context.setLineDash([]);
        }
        context.stroke();
        context.globalAlpha = 1;
      });

      // Draw nodes (larger size, perfectly round)
      nodes.forEach((node) => {
        const radius = 18; // Larger nodes
        
        context.save(); // Save context state for perfect circles
        
        // Draw glow effect
        const gradient = context.createRadialGradient(
          node.x, node.y, 0,
          node.x, node.y, radius * 2.5
        );
        // Convert hex to rgba for gradient
        const hexToRgba = (hex, alpha) => {
          const r = parseInt(hex.slice(1, 3), 16);
          const g = parseInt(hex.slice(3, 5), 16);
          const b = parseInt(hex.slice(5, 7), 16);
          return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        };
        
        gradient.addColorStop(0, hexToRgba(node.color, 0.7));
        gradient.addColorStop(0.5, hexToRgba(node.color, 0.4));
        gradient.addColorStop(1, hexToRgba(node.color, 0));
        
        // Draw glow with perfect circle
        context.beginPath();
        context.arc(node.x, node.y, radius * 2.5, 0, Math.PI * 2, false);
        context.fillStyle = gradient;
        context.fill();
        
        // Draw main node (perfectly round)
        context.beginPath();
        context.arc(node.x, node.y, radius, 0, Math.PI * 2, false);
        context.fillStyle = node.color;
        context.globalAlpha = 1.0;
        context.fill();
        
        // Draw border (perfectly round)
        context.beginPath();
        context.arc(node.x, node.y, radius, 0, Math.PI * 2, false);
        context.strokeStyle = node.color;
        context.lineWidth = 2.5;
        context.globalAlpha = 0.9;
        context.stroke();
        
        context.restore(); // Restore context state
        context.globalAlpha = 1;
      });
    };

    // Animation loop
    const animate = () => {
      render();
      animationFrame = requestAnimationFrame(animate);
    };

    animate();
  });

  onDestroy(() => {
    if (animationFrame) {
      cancelAnimationFrame(animationFrame);
    }
  });
</script>

<canvas
  bind:this={canvasElement}
  class={className}
  style="position: absolute; top: 0; left: 0; pointer-events: none;"
></canvas>
