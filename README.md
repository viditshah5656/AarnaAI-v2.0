# AarnaAI - Quantitative Intelligence System
> Markets decoded. Intelligence amplified.

This document outlines the UI architecture, design system, and UX philosophy of the AarnaAI prototype, built to the specifications of the "futuristic quantitative market prediction interface" design brief.

## 1. Full UI Layout Structure

The application is a single-page application (SPA) built on a CSS Grid-based layout. The core structure is defined in `index.html` and is consistent across all views.

- **`#app-container` (Grid Root)**: The main application wrapper, divided into two columns: the navigation and the main content.
    - **`.neural-nav` (Column 1)**: The primary neural navigation bar on the left. It is collapsed by default and expands on hover.
    - **`.main-wrapper` (Column 2)**: Contains the rest of the UI, split into a top bar and the main content area.
        - **`.context-bar` (Row 1)**: The context-aware top bar, displaying dynamic information.
        - **`.main-content` (Row 2)**: The primary workspace where different views (`Dashboard`, `Analyze`, etc.) are rendered by JavaScript.

## 2. Component Hierarchy

The UI is built with a component-based mindset, where each major section is a self-contained unit.

- **`Dashboard`** (`#dashboard-grid`)
    - **`Quant Signals Stack`** (`#quant-signals`)
        - `Signal Card`: Contains icon, title, value, and a micro-visualization (`.momentum-bar`, `.volatility-shape`, etc.).
    - **`Market Intelligence Core`** (`#market-consciousness` -> `#intelligence-core`)
        - `Time Horizon Selector`
        - `Prediction Arrow`
        - `Confidence Dial` (SVG-based)
        - `Model Consensus` visualization
    - **`Risk & Probability Matrix`** (`#risk-matrix`)
        - `Risk Cone Visualization` (CSS-based placeholder)
        - `Tail Risk Alerts`
- **`Analyze Page`** (`#analyze-page`)
    - `Model Selector`: A list of selectable `.model-card` components.
    - `Hyperparameter Controls`: A grid of advanced `.param-slider` components.
    - `Real-time Effect Preview`: A placeholder panel.
- **`News Intelligence Page`** (`#news-page`)
    - `Theme Clusters`: A list of topics.
    - `Influence Graph`: A styled placeholder representing a knowledge graph.
    - `News Impact Details`: A panel for detailed analysis.
- **`Strategy Lab Page`** (`#strategy-lab-page`)
    - `Signal Library`: A list of draggable `.lab-signal-card` components.
    - `Strategy Canvas`: A placeholder for visual strategy building.
    - `Simulation Outcome`: A placeholder for results.


## 3. Motion Behavior Description

Motion is used to convey information and enhance the feeling of a living, intelligent system.

- **Neural Navigation Expansion**: The nav bar smoothly expands on hover, revealing labels. This follows the principle of "hover = insight" without permanently occupying screen real estate.
- **Page Transitions (`page-load-in`)**: When navigating between views, the new content animates in with a subtle upward slide and fade. This provides a smooth, non-jarring transition.
- **"Breathing" Intelligence Core**: The central dashboard module has a slow, subtle scaling animation (`core-breathe`) to make it feel alive and constantly processing.
- **Pulsing Elements**: Key active elements, like the active nav item's indicator (`.nav-pulse`) or the prediction arrow, have a soft pulse animation. This draws attention to important states without being distracting.
- **"Thinking" Loader**: A custom loader animation (`.thinking-loader`) was designed to replace traditional spinners, visually representing the concept of "intelligence thinking".
- **Insightful Hovers**: Hovering over a signal card reveals a tooltip with its historical reliability, providing deeper information on demand.

## 4. Color & Typography System

The design system is defined in `style.css` under the `:root` selector, adhering to the "quant-futurist" aesthetic.

- **Color**:
    - **Base**: Deep space black (`--neural-black`) and graphite (`--neural-graphite`) create a dark, focused environment suitable for long hours of analysis.
    - **Accents**: Electric Cyan (`--accent-cyan`) is used as the primary interactive color. Neural Violet, Confidence Green, and Amber are used for semantic meaning (e.g., volatility, positive/negative outcomes, warnings).
    - **Purpose**: Colors are not decorative; they encode meaning. Green consistently represents positive or confident states, red/amber for risk, and violet/cyan for neutral or informational data.

- **Typography**:
    - **`--font-interface` ('Inter')**: A clean, technical sans-serif is used for all UI labels and text for maximum clarity.
    - **`--font-quant` ('JetBrains Mono')**: A monospace font is used for all numerical data, signal values, and identifiers. This provides a precise, "quant" feel and ensures that numbers align perfectly for easy comparison.

## 5. UX Reasoning

Every design choice was made to support the core philosophy of creating a cognitive co-pilot, not just a tool.

- **Information Density**: The UI is dense with information, but uses progressive disclosure (e.g., hover effects, collapsed nav) to prevent overwhelming the user. The most critical information is always visible, while secondary data is available on interaction.
- **Reducing Cognitive Load**: The default collapsed navigation, the clear visual hierarchy, and the use of intuitive micro-visualizations (like the momentum bar) are all designed to allow the user to absorb the market state at a glance without needing to parse raw numbers.
- **Visual-Mathematical Intuition**: The hyperparameter controls on the "Analyze" page use sliders instead of raw number inputs. This allows the user to develop an intuitive "feel" for how parameters affect the model, rather than just thinking in abstract numbers.
- **Avoiding Panic Bias**: As requested, a bright red is used sparingly. Warnings are primarily represented by Amber, reserving strong red for critical risk alerts, thereby preventing alarm fatigue.
- **Centralized Intelligence**: The "Market Consciousness View" is the focal point of the dashboard. It centralizes the most important output of the AI (direction, confidence) so the user has a single source of truth to start their analysis from.

## 6. Future Scalability Considerations

The current structure is designed to be easily extended.

- **Component-Based JS**: The `render...()` functions in `script.js` allow for new pages to be added easily. Simply create a new render function and add it to the `navigateTo` switch statement.
- **Centralized CSS Variables**: The entire visual theme (colors, fonts, spacing) can be updated by changing the variables in the `:root`. This makes rebranding or creating new themes (e.g., a high-contrast light theme) trivial.
- **Data-Driven UI**: Currently, the UI is static. The next step would be to connect the render functions to a live data feed or API. The JavaScript functions can be modified to accept data objects and render the UI dynamically based on that data, without needing to change the underlying HTML or CSS structure. For example, the `renderDashboard` function could take a `marketData` object and update the signal values and confidence dials accordingly.
