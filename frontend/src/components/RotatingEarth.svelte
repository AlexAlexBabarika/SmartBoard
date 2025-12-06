<script>
  import { onMount, onDestroy } from "svelte";
  import * as d3 from "d3";

  export let width = 800;
  export let height = 600;
  export let className = "";

  let canvasElement;
  let isLoading = true;
  let error = null;
  let rotationTimer = null;

  onMount(() => {
    if (!canvasElement) return;

    const canvas = canvasElement;
    const context = canvas.getContext("2d");
    if (!context) return;

    // Set up responsive dimensions
    const containerWidth = Math.min(width, window.innerWidth - 40);
    const containerHeight = Math.min(height, window.innerHeight - 100);
    const radius = Math.min(containerWidth, containerHeight) / 2.5;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = containerWidth * dpr;
    canvas.height = containerHeight * dpr;
    canvas.style.width = `${containerWidth}px`;
    canvas.style.height = `${containerHeight}px`;
    context.scale(dpr, dpr);

    // Create projection and path generator for Canvas
    const projection = d3
      .geoOrthographic()
      .scale(radius)
      .translate([containerWidth / 2, containerHeight / 2])
      .clipAngle(90);

    const path = d3.geoPath().projection(projection).context(context);

    const pointInPolygon = (point, polygon) => {
      const [x, y] = point;
      let inside = false;

      for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
        const [xi, yi] = polygon[i];
        const [xj, yj] = polygon[j];

        if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) {
          inside = !inside;
        }
      }

      return inside;
    };

    const pointInFeature = (point, feature) => {
      const geometry = feature.geometry;

      if (geometry.type === "Polygon") {
        const coordinates = geometry.coordinates;
        // Check if point is in outer ring
        if (!pointInPolygon(point, coordinates[0])) {
          return false;
        }
        // Check if point is in any hole (inner rings)
        for (let i = 1; i < coordinates.length; i++) {
          if (pointInPolygon(point, coordinates[i])) {
            return false; // Point is in a hole
          }
        }
        return true;
      } else if (geometry.type === "MultiPolygon") {
        // Check each polygon in the MultiPolygon
        for (const polygon of geometry.coordinates) {
          // Check if point is in outer ring
          if (pointInPolygon(point, polygon[0])) {
            // Check if point is in any hole
            let inHole = false;
            for (let i = 1; i < polygon.length; i++) {
              if (pointInPolygon(point, polygon[i])) {
                inHole = true;
                break;
              }
            }
            if (!inHole) {
              return true;
            }
          }
        }
        return false;
      }

      return false;
    };

    const generateDotsInPolygon = (feature, dotSpacing = 16) => {
      const dots = [];
      const bounds = d3.geoBounds(feature);
      const [[minLng, minLat], [maxLng, maxLat]] = bounds;

      const stepSize = dotSpacing * 0.08;
      let pointsGenerated = 0;

      for (let lng = minLng; lng <= maxLng; lng += stepSize) {
        for (let lat = minLat; lat <= maxLat; lat += stepSize) {
          const point = [lng, lat];
          if (pointInFeature(point, feature)) {
            dots.push(point);
            pointsGenerated++;
          }
        }
      }

      console.log(
        `[v0] Generated ${pointsGenerated} points for land feature:`,
        feature.properties?.featurecla || "Land",
      );
      return dots;
    };

    const allDots = [];
    let landFeatures;

    // Green animated dots (only on land)
    const rgbDots = [];
    const numRgbDots = 100;
    
    // Function to generate green dots only on land
    const generateGreenDotsOnLand = () => {
      rgbDots.length = 0; // Clear existing dots
      let dotsGenerated = 0;
      let attempts = 0;
      const maxAttempts = 5000;
      
      while (dotsGenerated < numRgbDots && attempts < maxAttempts) {
        attempts++;
        const lng = Math.random() * 360 - 180;
        const lat = (Math.random() - 0.5) * 180;
        const point = [lng, lat];
        
        // Exclude Antarctica (latitude below -60)
        if (lat < -60) {
          continue;
        }
        
        // Check if point is on land
        let isOnLand = false;
        if (landFeatures) {
          for (const feature of landFeatures.features) {
            if (pointInFeature(point, feature)) {
              isOnLand = true;
              break;
            }
          }
        }
        
        if (isOnLand) {
          // Generate different shades of green with smaller color range
          // Green component: 150-220 (narrower range of greens)
          // Red component: 0-30 (smaller red tint for less variation)
          // Blue component: 0-40 (smaller blue tint for less variation)
          const greenBase = 150 + Math.random() * 70; // 150-220
          const redTint = Math.random() * 30; // 0-30
          const blueTint = Math.random() * 40; // 0-40
          
          const color = [
            Math.floor(redTint),
            Math.floor(greenBase),
            Math.floor(blueTint)
          ];
          
          rgbDots.push({
            lng,
            lat,
            color,
            opacity: Math.random(), // Start with random opacity
            visible: Math.random() > 0.5, // Random initial visibility
            fadeSpeed: 0.02 + Math.random() * 0.03, // Slightly faster fade
            changeTimer: Math.random() * 80 + 40 // Shorter lifetime: 40-120 frames
          });
          dotsGenerated++;
        }
      }
      
      console.log(`Generated ${dotsGenerated} green dots on land after ${attempts} attempts`);
    };

    // Animate RGB dots appearance/disappearance
    const animateRgbDots = () => {
      rgbDots.forEach((dot) => {
        dot.changeTimer--;
        
        if (dot.changeTimer <= 0) {
          // Toggle visibility
          dot.visible = !dot.visible;
          dot.changeTimer = Math.random() * 80 + 40; // Shorter lifetime: 40-120 frames
        }
        
        if (dot.visible) {
          // Fade in
          dot.opacity = Math.min(1, dot.opacity + dot.fadeSpeed);
        } else {
          // Fade out
          dot.opacity = Math.max(0, dot.opacity - dot.fadeSpeed);
        }
      });
    };

    const render = () => {
      // Clear canvas
      context.clearRect(0, 0, containerWidth, containerHeight);

      const currentScale = projection.scale();
      const scaleFactor = currentScale / radius;

      // Draw ocean (globe background)
      context.beginPath();
      context.arc(containerWidth / 2, containerHeight / 2, currentScale, 0, 2 * Math.PI);
      context.fillStyle = "#000000";
      context.fill();
      context.strokeStyle = "#ffffff";
      context.lineWidth = 2 * scaleFactor;
      context.stroke();

      if (landFeatures) {
        // Draw graticule
        const graticule = d3.geoGraticule();
        context.beginPath();
        path(graticule());
        context.strokeStyle = "#ffffff";
        context.lineWidth = 1 * scaleFactor;
        context.globalAlpha = 0.25;
        context.stroke();
        context.globalAlpha = 1;

        // Draw land outlines
        context.beginPath();
        landFeatures.features.forEach((feature) => {
          path(feature);
        });
        context.strokeStyle = "#ffffff";
        context.lineWidth = 1 * scaleFactor;
        context.stroke();

        // Draw halftone dots
        allDots.forEach((dot) => {
          const projected = projection([dot.lng, dot.lat]);
          if (
            projected &&
            projected[0] >= 0 &&
            projected[0] <= containerWidth &&
            projected[1] >= 0 &&
            projected[1] <= containerHeight
          ) {
            context.beginPath();
            context.arc(projected[0], projected[1], 1.2 * scaleFactor, 0, 2 * Math.PI);
            context.fillStyle = "#999999";
            context.fill();
          }
        });

        // Draw animated green dots (only on land)
        animateRgbDots();
        rgbDots.forEach((dot) => {
          const projected = projection([dot.lng, dot.lat]);
          if (
            projected &&
            projected[0] >= 0 &&
            projected[0] <= containerWidth &&
            projected[1] >= 0 &&
            projected[1] <= containerHeight &&
            dot.opacity > 0
          ) {
            const size = 2.5 * scaleFactor * dot.opacity;
            context.beginPath();
            context.arc(projected[0], projected[1], size, 0, 2 * Math.PI);
            context.fillStyle = `rgba(${dot.color[0]}, ${dot.color[1]}, ${dot.color[2]}, ${dot.opacity})`;
            context.fill();
            
            // Add glow effect for green dots
            context.shadowBlur = 12 * dot.opacity;
            context.shadowColor = `rgba(${dot.color[0]}, ${dot.color[1]}, ${dot.color[2]}, ${dot.opacity * 0.6})`;
            context.beginPath();
            context.arc(projected[0], projected[1], size * 1.8, 0, 2 * Math.PI);
            context.fill();
            context.shadowBlur = 0;
          }
        });
      }
    };

    const loadWorldData = async () => {
      try {
        isLoading = true;

        const response = await fetch(
          "https://raw.githubusercontent.com/martynafford/natural-earth-geojson/refs/heads/master/110m/physical/ne_110m_land.json",
        );
        if (!response.ok) throw new Error("Failed to load land data");

        landFeatures = await response.json();

        // Generate dots for all land features
        let totalDots = 0;
        landFeatures.features.forEach((feature) => {
          const dots = generateDotsInPolygon(feature, 16);
          dots.forEach(([lng, lat]) => {
            allDots.push({ lng, lat, visible: true });
            totalDots++;
          });
        });

        console.log(`[v0] Total dots generated: ${totalDots} across ${landFeatures.features.length} land features`);

        // Generate green dots on land after land features are loaded
        generateGreenDotsOnLand();

        render();
        isLoading = false;
      } catch (err) {
        error = "Failed to load land map data";
        isLoading = false;
      }
    };

    // Set up rotation and interaction
    const rotation = [0, 0];
    let autoRotate = true;
    const rotationSpeed = 0.5;

    const rotate = () => {
      if (autoRotate) {
        rotation[0] += rotationSpeed;
        projection.rotate(rotation);
      }
      render(); // Always render to animate RGB dots
    };

    // Auto-rotation timer
    rotationTimer = d3.timer(rotate);

    const handleMouseDown = (event) => {
      autoRotate = false;
      const startX = event.clientX;
      const startY = event.clientY;
      const startRotation = [...rotation];

      const handleMouseMove = (moveEvent) => {
        const sensitivity = 0.5;
        const dx = moveEvent.clientX - startX;
        const dy = moveEvent.clientY - startY;

        rotation[0] = startRotation[0] + dx * sensitivity;
        rotation[1] = startRotation[1] - dy * sensitivity;
        rotation[1] = Math.max(-90, Math.min(90, rotation[1]));

        projection.rotate(rotation);
        render();
      };

      const handleMouseUp = () => {
        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);

        setTimeout(() => {
          autoRotate = true;
        }, 10);
      };

      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    };

    const handleWheel = (event) => {
      event.preventDefault();
      const scaleFactor = event.deltaY > 0 ? 0.9 : 1.1;
      const newRadius = Math.max(radius * 0.5, Math.min(radius * 3, projection.scale() * scaleFactor));
      projection.scale(newRadius);
      render();
    };

    canvas.addEventListener("mousedown", handleMouseDown);
    canvas.addEventListener("wheel", handleWheel);

    // Load the world data
    loadWorldData();

    // Cleanup function
    return () => {
      if (rotationTimer) {
        rotationTimer.stop();
      }
      canvas.removeEventListener("mousedown", handleMouseDown);
      canvas.removeEventListener("wheel", handleWheel);
    };
  });

  onDestroy(() => {
    if (rotationTimer) {
      rotationTimer.stop();
    }
  });
</script>

{#if error}
  <div class="dark flex items-center justify-center bg-pe-card rounded-pe-lg p-8 {className}">
    <div class="text-center">
      <p class="dark text-red-500 font-semibold mb-2">Error loading Earth visualization</p>
      <p class="dark text-pe-muted text-sm">{error}</p>
    </div>
  </div>
{:else}
  <div class="relative {className}">
    <canvas
      bind:this={canvasElement}
      class="w-full h-full bg-transparent dark"
      style="object-fit: contain;"
    />
    {#if !className.includes('opacity')}
      <div class="absolute bottom-4 left-4 text-xs text-pe-muted px-2 py-1 rounded-md dark bg-pe-panel">
        Drag to rotate • Scroll to zoom
      </div>
    {/if}
  </div>
{/if}
