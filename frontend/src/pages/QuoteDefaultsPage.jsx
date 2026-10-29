import React, { useState } from 'react';
import { Plus, X, Save, CheckCircle2 } from 'lucide-react';
import TopHeader from '../components/TopHeader';

export default function QuoteDefaultsPage({
  quoteDefaults,
  onSaveDefaults,
}) {
  const [defaults, setDefaults] = useState(quoteDefaults);
  const [newCurrency, setNewCurrency] = useState('');
  const [showAddCurrency, setShowAddCurrency] = useState(false);
  const [newProductType, setNewProductType] = useState('');
  const [showAddType, setShowAddType] = useState(false);
  const [newUnit, setNewUnit] = useState('');
  const [showAddUnit, setShowAddUnit] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveToast, setSaveToast] = useState(false);

  // Currency handlers
  const handleAddCurrency = () => {
    if (!newCurrency.trim()) return;
    const code = newCurrency.trim().toUpperCase();
    if (!defaults.currencies.includes(code)) {
      setDefaults({
        ...defaults,
        currencies: [...defaults.currencies, code],
      });
    }
    setNewCurrency('');
    setShowAddCurrency(false);
  };

  const handleRemoveCurrency = (curr) => {
    if (curr === defaults.defaultCurrency) return; // cannot remove default
    setDefaults({
      ...defaults,
      currencies: defaults.currencies.filter((c) => c !== curr),
    });
  };

  // Product type handlers
  const handleAddProductType = () => {
    if (!newProductType.trim()) return;
    const type = newProductType.trim();
    if (!defaults.hairProductTypes.includes(type)) {
      setDefaults({
        ...defaults,
        hairProductTypes: [...defaults.hairProductTypes, type],
      });
    }
    setNewProductType('');
    setShowAddType(false);
  };

  const handleRemoveProductType = (t) => {
    setDefaults({
      ...defaults,
      hairProductTypes: defaults.hairProductTypes.filter((type) => type !== t),
    });
  };

  // Unit handlers
  const handleAddUnit = () => {
    if (!newUnit.trim()) return;
    const u = newUnit.trim().toLowerCase();
    if (!defaults.units.includes(u)) {
      setDefaults({
        ...defaults,
        units: [...defaults.units, u],
      });
    }
    setNewUnit('');
    setShowAddUnit(false);
  };

  const handleRemoveUnit = (u) => {
    if (u === defaults.defaultUnit) return;
    setDefaults({
      ...defaults,
      units: defaults.units.filter((unit) => unit !== u),
    });
  };

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      onSaveDefaults(defaults);
      setSaveToast(true);
      setTimeout(() => setSaveToast(false), 2500);
    }, 350);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
      <TopHeader
        title="Quote defaults"
        subtitle="App-wide defaults for new subscribers"
        actions={
          <button
            className="btn-primary"
            onClick={handleSave}
            disabled={isSaving}
            id="btn-save-quote-defaults"
          >
            <Save size={14} />
            <span>{isSaving ? 'Saving...' : 'Save changes'}</span>
          </button>
        }
      />

      <div className="page-body">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 20 }}>
          {/* Left Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Currencies */}
            <div className="card">
              <div style={{ marginBottom: 12 }}>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-heading)' }}>Currencies</h3>
                <p style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>* = default for new subscribers</p>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
                {defaults.currencies.map((c) => {
                  const isDef = c === defaults.defaultCurrency;
                  return (
                    <span
                      key={c}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 6,
                        padding: '5px 12px',
                        borderRadius: 'var(--radius-full)',
                        fontSize: 12.5,
                        fontWeight: 600,
                        backgroundColor: isDef ? 'var(--status-trial-bg)' : '#F1F5F9',
                        color: isDef ? 'var(--primary)' : 'var(--text-body)',
                        border: '1px solid',
                        borderColor: isDef ? 'var(--primary-border)' : '#E2E8F0',
                      }}
                    >
                      <span>{c} {isDef && '★'}</span>
                      {!isDef && (
                        <button
                          type="button"
                          onClick={() => handleRemoveCurrency(c)}
                          style={{ color: 'var(--text-light)', padding: 0 }}
                        >
                          <X size={12} />
                        </button>
                      )}
                    </span>
                  );
                })}

                {showAddCurrency ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <input
                      type="text"
                      className="input-text"
                      style={{ width: 80, padding: '4px 8px', fontSize: 12 }}
                      placeholder="e.g. AUD"
                      value={newCurrency}
                      onChange={(e) => setNewCurrency(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddCurrency()}
                      autoFocus
                    />
                    <button className="btn-primary" onClick={handleAddCurrency} style={{ padding: '4px 8px', fontSize: 11 }}>
                      Add
                    </button>
                    <button className="btn-secondary" onClick={() => setShowAddCurrency(false)} style={{ padding: '4px 8px', fontSize: 11 }}>
                      ✕
                    </button>
                  </div>
                ) : (
                  <button
                    className="btn-secondary"
                    onClick={() => setShowAddCurrency(true)}
                    style={{ padding: '5px 12px', fontSize: 12 }}
                  >
                    <Plus size={13} />
                    <span>Add</span>
                  </button>
                )}
              </div>
            </div>

            {/* Tax / VAT */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-heading)' }}>Tax / VAT</h3>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: 14 }}>
                <div className="form-group">
                  <label className="form-label">Default rate</label>
                  <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                    <input
                      type="number"
                      className="input-text"
                      style={{ width: '100%', paddingRight: 28 }}
                      value={defaults.taxVat.defaultRate}
                      onChange={(e) =>
                        setDefaults({
                          ...defaults,
                          taxVat: { ...defaults.taxVat, defaultRate: Number(e.target.value) },
                        })
                      }
                    />
                    <span style={{ position: 'absolute', right: 12, color: 'var(--text-light)', fontSize: 12.5 }}>%</span>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Label on PDF</label>
                  <input
                    type="text"
                    className="input-text"
                    value={defaults.taxVat.labelOnPdf}
                    onChange={(e) =>
                      setDefaults({
                        ...defaults,
                        taxVat: { ...defaults.taxVat, labelOnPdf: e.target.value },
                      })
                    }
                  />
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 6, borderTop: '1px solid var(--card-border)' }}>
                <div>
                  <div className="form-label">Per-line taxability</div>
                  <div className="form-sublabel">Subscribers can mark lines as non-taxable</div>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={defaults.taxVat.perLineTaxability}
                    onChange={(e) =>
                      setDefaults({
                        ...defaults,
                        taxVat: { ...defaults.taxVat, perLineTaxability: e.target.checked },
                      })
                    }
                  />
                  <span className="slider" />
                </label>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div className="form-label">Prices include tax</div>
                  <div className="form-sublabel">Off = tax added on top of subtotal</div>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={defaults.taxVat.pricesIncludeTax}
                    onChange={(e) =>
                      setDefaults({
                        ...defaults,
                        taxVat: { ...defaults.taxVat, pricesIncludeTax: e.target.checked },
                      })
                    }
                  />
                  <span className="slider" />
                </label>
              </div>
            </div>

            {/* Default Deposit */}
            <div className="card">
              <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-heading)', marginBottom: 14 }}>
                Default deposit
              </h3>

              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div className="tab-list">
                  <button
                    className={`tab-btn ${defaults.defaultDeposit.type === 'percent' ? 'active' : ''}`}
                    onClick={() =>
                      setDefaults({
                        ...defaults,
                        defaultDeposit: { ...defaults.defaultDeposit, type: 'percent' },
                      })
                    }
                  >
                    % of total
                  </button>
                  <button
                    className={`tab-btn ${defaults.defaultDeposit.type === 'fixed' ? 'active' : ''}`}
                    onClick={() =>
                      setDefaults({
                        ...defaults,
                        defaultDeposit: { ...defaults.defaultDeposit, type: 'fixed' },
                      })
                    }
                  >
                    Fixed amount
                  </button>
                </div>

                <div style={{ position: 'relative', display: 'flex', alignItems: 'center', width: 90 }}>
                  <input
                    type="number"
                    className="input-text"
                    style={{ width: '100%', paddingRight: 26 }}
                    value={defaults.defaultDeposit.amount}
                    onChange={(e) =>
                      setDefaults({
                        ...defaults,
                        defaultDeposit: {
                          ...defaults.defaultDeposit,
                          amount: Number(e.target.value),
                        },
                      })
                    }
                  />
                  <span style={{ position: 'absolute', right: 10, color: 'var(--text-light)', fontSize: 12 }}>
                    {defaults.defaultDeposit.type === 'percent' ? '%' : defaults.defaultCurrency}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Hair Product Types */}
            <div className="card">
              <div style={{ marginBottom: 12 }}>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-heading)' }}>Hair product types</h3>
                <p style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>Shown when adding a product</p>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
                {defaults.hairProductTypes.map((t) => (
                  <span
                    key={t}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 6,
                      padding: '5px 12px',
                      borderRadius: 'var(--radius-full)',
                      fontSize: 12.5,
                      backgroundColor: '#F1F5F9',
                      color: 'var(--text-body)',
                      border: '1px solid #E2E8F0',
                    }}
                  >
                    <span>{t}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveProductType(t)}
                      style={{ color: 'var(--text-light)', padding: 0 }}
                    >
                      <X size={12} />
                    </button>
                  </span>
                ))}

                {showAddType ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <input
                      type="text"
                      className="input-text"
                      style={{ width: 100, padding: '4px 8px', fontSize: 12 }}
                      placeholder="Type name"
                      value={newProductType}
                      onChange={(e) => setNewProductType(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddProductType()}
                      autoFocus
                    />
                    <button className="btn-primary" onClick={handleAddProductType} style={{ padding: '4px 8px', fontSize: 11 }}>
                      Add
                    </button>
                    <button className="btn-secondary" onClick={() => setShowAddType(false)} style={{ padding: '4px 8px', fontSize: 11 }}>
                      ✕
                    </button>
                  </div>
                ) : (
                  <button
                    className="btn-secondary"
                    onClick={() => setShowAddType(true)}
                    style={{ padding: '5px 12px', fontSize: 12 }}
                  >
                    <Plus size={13} />
                    <span>Add type</span>
                  </button>
                )}
              </div>
            </div>

            {/* Units */}
            <div className="card">
              <div style={{ marginBottom: 12 }}>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-heading)' }}>Units</h3>
                <p style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>* = default</p>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
                {defaults.units.map((u) => {
                  const isDef = u === defaults.defaultUnit;
                  return (
                    <span
                      key={u}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 6,
                        padding: '5px 12px',
                        borderRadius: 'var(--radius-full)',
                        fontSize: 12.5,
                        fontWeight: isDef ? 600 : 400,
                        backgroundColor: isDef ? 'var(--status-trial-bg)' : '#F1F5F9',
                        color: isDef ? 'var(--primary)' : 'var(--text-body)',
                        border: '1px solid',
                        borderColor: isDef ? 'var(--primary-border)' : '#E2E8F0',
                      }}
                    >
                      <span>{u} {isDef && '★'}</span>
                      {!isDef && (
                        <button
                          type="button"
                          onClick={() => handleRemoveUnit(u)}
                          style={{ color: 'var(--text-light)', padding: 0 }}
                        >
                          <X size={12} />
                        </button>
                      )}
                    </span>
                  );
                })}

                {showAddUnit ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <input
                      type="text"
                      className="input-text"
                      style={{ width: 80, padding: '4px 8px', fontSize: 12 }}
                      placeholder="unit"
                      value={newUnit}
                      onChange={(e) => setNewUnit(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddUnit()}
                      autoFocus
                    />
                    <button className="btn-primary" onClick={handleAddUnit} style={{ padding: '4px 8px', fontSize: 11 }}>
                      Add
                    </button>
                    <button className="btn-secondary" onClick={() => setShowAddUnit(false)} style={{ padding: '4px 8px', fontSize: 11 }}>
                      ✕
                    </button>
                  </div>
                ) : (
                  <button
                    className="btn-secondary"
                    onClick={() => setShowAddUnit(true)}
                    style={{ padding: '5px 12px', fontSize: 12 }}
                  >
                    <Plus size={13} />
                    <span>Add unit</span>
                  </button>
                )}
              </div>
            </div>

            {/* Numbering */}
            <div className="card">
              <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-heading)', marginBottom: 14 }}>
                Numbering
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                <div className="form-group">
                  <label className="form-label">Quote prefix</label>
                  <input
                    type="text"
                    className="input-text"
                    value={defaults.numbering.quotePrefix}
                    onChange={(e) =>
                      setDefaults({
                        ...defaults,
                        numbering: { ...defaults.numbering, quotePrefix: e.target.value },
                      })
                    }
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Invoice prefix</label>
                  <input
                    type="text"
                    className="input-text"
                    value={defaults.numbering.invoicePrefix}
                    onChange={(e) =>
                      setDefaults({
                        ...defaults,
                        numbering: { ...defaults.numbering, invoicePrefix: e.target.value },
                      })
                    }
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Start at</label>
                  <input
                    type="text"
                    className="input-text"
                    value={defaults.numbering.startAt}
                    onChange={(e) =>
                      setDefaults({
                        ...defaults,
                        numbering: { ...defaults.numbering, startAt: e.target.value },
                      })
                    }
                  />
                </div>
              </div>
            </div>

            {/* Default Note */}
            <div className="card">
              <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-heading)', marginBottom: 10 }}>
                Default note
              </h3>
              <textarea
                rows={3}
                className="input-text"
                style={{ width: '100%', resize: 'vertical', fontSize: 12.5 }}
                value={defaults.defaultNote}
                onChange={(e) => setDefaults({ ...defaults, defaultNote: e.target.value })}
              />
            </div>
          </div>
        </div>
      </div>

      {saveToast && (
        <div className="toast">
          <CheckCircle2 size={16} color="#4ADE80" />
          <span>Quote defaults saved successfully!</span>
        </div>
      )}
    </div>
  );
}
