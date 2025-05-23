
GRAPH_SCHEMA_DESCRIPTION = """
The knowledge graph contains information about microbial interactions and essential gene functions.

Key Node Labels:
- microbe: Represents a microbial strain.
  - Properties:
    - name (string, unique identifier)
- metabolite: Represents a chemical compound involved in interactions.
  - Properties:
    - name (string, unique identifier)
- pathway: Represents a biological pathway microbes are involved in.
  - Properties:
    - name (string, unique identifier)
- KO: Represents a KEGG Orthology (KO) term, indicating an essential gene function.
  - Properties:
    - name (string, unique identifier, the KO ID itself, e.g., "K00246")
    # Note: The description property is stored on the relationship, not the node itself in the current graph builder.


Key Relationship Types (with properties):
- [:PRODUCES] - (Microbe)-[:PRODUCES {flux: float, description: str}]->(Metabolite)
- [:CONSUMES] - (Metabolite)-[:CONSUMES {flux: float, description: str}]->(Microbe) # Note: Relationship direction in graph storage. Query typically reverses: (Microbe)<-[:CONSUMES]-(Metabolite)
- [:CROSS_FEEDS_WITH] - (Microbe)-[:CROSS_FEEDS_WITH {source_biomass: float, target_biomass: float}]->(Microbe)
- [:INVOLVED_IN] - (Microbe)-[:INVOLVED_IN {subsystem_score: float, description: str}]->(Pathway)
- [:HAS_KEGG_ORTHOLOGY] - (Microbe)-[:HAS_KEGG_ORTHOLOGY {description: str}]->(KO)
  - Description property example: "Bifidobacterium_longum_longum_JDM301 has an essential gene with kegg orthology (KO) of K00246 and the KO description is Succinate dehydrogenase"



Important Considerations for Queries:
- Always use parameters ($param_name) for node names or other values in WHERE clauses for security and efficiency.
- **Case Sensitivity**: Node name properties (e.g., Metabolite.name, Microbe.name) might have inconsistent capitalization. To ensure reliable matching regardless of case, **always use the `toLower()` function** on both the property and the parameter when matching names. Example: `WHERE toLower(met.name) = toLower($name)`.
- When searching for microbes related to a metabolite, consider both PRODUCES and CONSUMES relationships.
- Flux values indicate the rate of production/consumption. Higher flux might indicate higher importance.
- Abundance represents the relative presence of a microbe (if available).
- Subsystem score represents the importance of a pathway to a microbe.
- 'KO' nodes represent essential gene orthologies. The `HAS_KEGG_ORTHOLOGY` relationship links a microbe to a KO it possesses. The description on this relationship often contains the functional annotation of the KO.


Specific Query Patterns (Using Case-Insensitive Matching):
- To find entities doing *both* A and B (e.g., produce AND consume a specific metabolite):
  MATCH (met:Metabolite) WHERE toLower(met.name) = toLower($name) // Case-insensitive match first
  WITH met // Pass the matched metabolite
  MATCH (m:Microbe)-[:PRODUCES]->(met)
  MATCH (m)<-[:CONSUMES]-(met) // Find microbes with both relationships to 'met'
  RETURN m.name

- To calculate net values (e.g., net flux = production - consumption) for microbes doing *both*:
  MATCH (met:Metabolite) WHERE toLower(met.name) = toLower($name) // Case-insensitive match first
  WITH met
  MATCH (m:Microbe)-[p:PRODUCES]->(met)
  MATCH (m)<-[c:CONSUMES]-(met)
  RETURN m.name, p.flux AS production_flux, c.flux AS consumption_flux, (p.flux - c.flux) AS net_flux

- To handle cases where production or consumption might be missing (find microbes doing *either or both*), use OPTIONAL MATCH and COALESCE:
  MATCH (met:Metabolite) WHERE toLower(met.name) = toLower($name) // Case-insensitive match first
  WITH met
  MATCH (m:Microbe) // Consider adding WHERE clause if microbe list is too large
  OPTIONAL MATCH (m)-[p:PRODUCES]->(met)
  OPTIONAL MATCH (m)<-[c:CONSUMES]-(met)
  // Filter for microbes that have at least one interaction with the metabolite
  WHERE p IS NOT NULL OR c IS NOT NULL
  WITH m, met, COALESCE(p.flux, 0.0) AS production_flux, COALESCE(c.flux, 0.0) AS consumption_flux
  RETURN m.name, production_flux, consumption_flux, (production_flux - consumption_flux) AS net_flux
  ORDER BY net_flux DESC // Example ordering

- To find KOs associated with a specific microbe:
  MATCH (m:Microbe)-[r:HAS_KEGG_ORTHOLOGY]->(k:KO)
  WHERE toLower(m.name) = toLower($microbe_name)
  RETURN k.name AS ko_id, r.description AS ko_description

- To find microbes associated with a specific KO:
  MATCH (m:Microbe)-[r:HAS_KEGG_ORTHOLOGY]->(k:KO)
  WHERE toLower(k.name) = toLower($ko_id)
  RETURN m.name AS microbe_name, r.description AS relationship_description

- To find microbes that have a KO whose description contains a specific keyword (e.g., "dehydrogenase"):
  MATCH (m:Microbe)-[r:HAS_KEGG_ORTHOLOGY]->(k:KO)
  WHERE toLower(r.description) CONTAINS toLower($keyword)
  RETURN DISTINCT m.name AS microbe_name, k.name AS ko_id

Ensure all variables used in RETURN or calculations are defined in the preceding MATCH or WITH clauses. Use WITH clauses effectively to pass variables between MATCH clauses.
"""