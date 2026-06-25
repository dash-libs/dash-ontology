"""DashRelate interactive UI for Databricks notebooks."""
from __future__ import annotations


def launch():
    try:
        import ipywidgets as w
        from IPython.display import display
    except ImportError:
        raise RuntimeError("ipywidgets required. Run: %pip install ipywidgets")

    from dashrelate.ontology import OntologyBuilder

    ont_name = w.Text(description="Ontology name:", placeholder="My Data Ontology")
    ont_desc = w.Text(description="Description:", placeholder="Brief description for AI context")

    # Entity builder
    e_name = w.Text(description="Entity name:", placeholder="Customer")
    e_table = w.Text(description="UC Table:", placeholder="catalog.schema.dim_customer")
    e_pk = w.Text(description="Primary key:", value="id")
    e_desc = w.Text(description="Description:", placeholder="Describes a bank customer")
    e_tags = w.Text(description="Tags:", placeholder="pii, core (comma separated)")
    add_entity_btn = w.Button(description="＋ Add Entity", button_style="info")
    entity_output = w.Output()
    entities = []

    def on_add_entity(b):
        tags = [t.strip() for t in e_tags.value.split(",") if t.strip()]
        entities.append({
            "name": e_name.value.strip(), "table": e_table.value.strip(),
            "pk": e_pk.value.strip(), "description": e_desc.value.strip(), "tags": tags
        })
        with entity_output:
            entity_output.clear_output()
            for i, e in enumerate(entities, 1):
                print(f"  {i}. {e['name']} → {e['table']}")

    add_entity_btn.on_click(on_add_entity)

    # Relationship builder
    r_from = w.Text(description="From entity:", placeholder="Customer")
    r_to = w.Text(description="To entity:", placeholder="Account")
    r_from_col = w.Text(description="From column:", placeholder="customer_id")
    r_to_col = w.Text(description="To column:", placeholder="customer_id")
    r_type = w.Dropdown(options=["one_to_many", "many_to_many", "one_to_one"],
                        description="Type:")
    r_label = w.Text(description="Label:", placeholder="has_account")
    r_semantic = w.Text(description="AI semantic:", placeholder="A customer can hold one or more accounts")
    add_rel_btn = w.Button(description="＋ Add Relationship", button_style="info")
    rel_output = w.Output()
    relationships = []

    def on_add_rel(b):
        relationships.append({
            "from": r_from.value.strip(), "to": r_to.value.strip(),
            "from_col": r_from_col.value.strip(), "to_col": r_to_col.value.strip(),
            "type": r_type.value, "label": r_label.value.strip(),
            "semantic": r_semantic.value.strip()
        })
        with rel_output:
            rel_output.clear_output()
            for i, r in enumerate(relationships, 1):
                print(f"  {i}. {r['from']} —[{r['label']}]→ {r['to']}")

    add_rel_btn.on_click(on_add_rel)

    save_table = w.Text(description="Save to table:", placeholder="catalog.schema.ontology")
    run_btn = w.Button(description="💾 Save Ontology", button_style="success",
                       layout=w.Layout(height="40px"))
    validate_btn = w.Button(description="✅ Validate", button_style="warning")
    output = w.Output()

    def on_run(b):
        with output:
            output.clear_output()
            try:
                ont = OntologyBuilder(ont_name.value.strip(), ont_desc.value.strip())
                for e in entities:
                    ont.add_entity(e["name"], e["table"], e["description"], e["pk"], e["tags"])
                for r in relationships:
                    ont.add_relationship(r["from"], r["to"], r["from_col"], r["to_col"],
                                         r["type"], r["label"], r["semantic"])
                issues = ont.validate()
                if issues:
                    for i in issues:
                        print(f"⚠️  {i}")
                    return
                if save_table.value.strip():
                    ont.save(save_table.value.strip())
                ont.summary()
            except Exception as e:
                print(f"❌ {e}")

    def on_validate(b):
        with output:
            output.clear_output()
            try:
                ont = OntologyBuilder(ont_name.value.strip())
                for e in entities:
                    ont.add_entity(e["name"], e["table"], e["description"], e["pk"], e["tags"])
                for r in relationships:
                    ont.add_relationship(r["from"], r["to"], r["from_col"], r["to_col"],
                                         r["type"], r["label"], r["semantic"])
                ont.summary()
            except Exception as e:
                print(f"❌ {e}")

    run_btn.on_click(on_run)
    validate_btn.on_click(on_validate)

    ui = w.VBox([
        w.HTML("<h2 style='color:#4527A0'>🕸️ DashRelate — Ontology & Lineage</h2>"),
        w.HTML("<b>Ontology</b>"), ont_name, ont_desc,
        w.HTML("<hr><b>Entities</b>"),
        w.HBox([e_name, e_table, e_pk]), w.HBox([e_desc, e_tags]), add_entity_btn, entity_output,
        w.HTML("<hr><b>Relationships</b>"),
        w.HBox([r_from, r_to, r_type]),
        w.HBox([r_from_col, r_to_col]),
        w.HBox([r_label, r_semantic]),
        add_rel_btn, rel_output,
        w.HTML("<hr>"), save_table,
        w.HBox([validate_btn, run_btn]),
        output,
    ], layout=w.Layout(padding="16px", border="1px solid #ddd", border_radius="8px"))

    display(ui)
