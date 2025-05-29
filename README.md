# ♿ Accessible Route Optimizer

A Python-based routing engine that finds the most accessible public transit paths for people with mobility needs. Built using Dijkstra's algorithm and designed to follow AODA compliance standards.

---

## 🚀 Features

- **Graph-based routing** using NetworkX
- **Accessibility-aware pathfinding** (avoids stairs, includes elevator outages)
- **Flexible data input** via CSV or GeoJSON transit maps
- **Fast shortest-path computation** using Dijkstra's algorithm
- **Real-time updates** ready for dashboard integration
- **AODA compliance** focused design

---

## 🧠 How It Works

1. **Load transit map** (nodes = stops/stations, edges = routes)
2. **Tag accessibility features** (elevator, low-floor, wheelchair access)
3. **Compute optimal path** based on user accessibility needs
4. **Return best route** avoiding inaccessible elements

---

## 🔧 Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/your_username/accessible-route-optimizer.git
cd accessible-route-optimizer
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run an example
```bash
python src/main.py --start "Union Station" --end "Yorkdale" --accessible-only
```

---

## 🛠 Tech Stack

- **Python 3.10+**
- **NetworkX** - Graph data structures and algorithms
- **Pandas** - Data manipulation and analysis
- **Matplotlib** - Data visualization
- **GeoJSON** - Geospatial data support (optional)

---

## 📁 Project Structure

```
accessible-route-optimizer/
├── src/
│   ├── main.py              # Entry point
│   ├── routing_engine.py    # Core routing logic
│   ├── accessibility.py     # Accessibility filters
│   └── data_loader.py       # Data input handlers
├── data/
│   ├── sample_transit.csv   # Sample transit data
│   └── accessibility.json   # Accessibility metadata
├── tests/
│   └── test_routing.py      # Unit tests
├── requirements.txt
└── README.md
```

---

## 🚌 Usage Examples

### Basic routing
```python
from src.routing_engine import AccessibleRouter

router = AccessibleRouter('data/sample_transit.csv')
path = router.find_path(start="Union Station", end="Yorkdale")
print(f"Best route: {' → '.join(path)}")
```

### Accessibility-only routing
```python
path = router.find_accessible_path(
    start="Union Station", 
    end="Yorkdale",
    requirements=['wheelchair_accessible', 'no_stairs']
)
```

### Real-time updates
```python
# Report elevator outage
router.update_accessibility("Bloor Station", elevator_working=False)
path = router.find_accessible_path("Dundas", "St. George")
```

---

## 📊 Data Format

### Transit Network CSV
```csv
from_stop,to_stop,route_id,travel_time,wheelchair_accessible,has_elevator
Union Station,King,1,3,true,true
King,Queen,1,2,true,false
```

### Accessibility Metadata JSON
```json
{
  "Union Station": {
    "wheelchair_accessible": true,
    "has_elevator": true,
    "elevator_working": true,
    "platform_gap": "small"
  }
}
```

---

## 🎯 Roadmap

- [ ] **Real-time data integration** (GTFS-RT support)
- [ ] **Web dashboard** for route visualization
- [ ] **Mobile app integration** via REST API
- [ ] **Multi-modal routing** (bus + subway + walking)
- [ ] **Crowdsourced accessibility reports**
- [ ] **Voice navigation** support

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your_username/accessible-route-optimizer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your_username/accessible-route-optimizer/discussions)
- **Email**: accessibility-support@yourproject.com

---

## 🙏 Acknowledgments

- **AODA Standards** for accessibility guidelines
- **OpenStreetMap** community for transit data
- **NetworkX** team for graph algorithms
- **Accessibility advocates** who provided feedback and testing

---

*Built with ❤️ for creating more inclusive public transit experiences.*
