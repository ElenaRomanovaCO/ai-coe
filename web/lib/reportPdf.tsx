// Client-side PDF rendering for the Client Maturity Report (FR-060). Imported
// dynamically (await import("@/lib/reportPdf")) from the editor's Export handler so
// @react-pdf/renderer stays out of the SSR/main bundle and only loads in the browser
// on demand. Renders the structured sections — not the markdown — so the PDF layout is
// controlled here, independent of the on-screen preview.

import {
  Document,
  Page,
  StyleSheet,
  Text,
  View,
  pdf,
} from "@react-pdf/renderer";

import { isListSection, type SectionValue } from "@/lib/reports";

export interface ReportPdfInput {
  report_id: string;
  title: string;
  preparedFor: string;
  sections: Record<string, SectionValue>;
  section_order: string[];
  section_titles: Record<string, string>;
}

const styles = StyleSheet.create({
  page: { paddingVertical: 48, paddingHorizontal: 56, fontSize: 11, color: "#1e293b" },
  title: { fontSize: 22, fontWeight: 700, color: "#0f172a", marginBottom: 4 },
  meta: { fontSize: 9, color: "#64748b", marginBottom: 24 },
  section: { marginBottom: 16 },
  heading: {
    fontSize: 12,
    fontWeight: 700,
    color: "#4338ca",
    marginBottom: 5,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  paragraph: { fontSize: 11, lineHeight: 1.5, color: "#334155" },
  listItem: { flexDirection: "row", marginBottom: 3 },
  bullet: { width: 12, fontSize: 11, color: "#4338ca" },
  listText: { flex: 1, fontSize: 11, lineHeight: 1.4, color: "#334155" },
});

function ReportDocument({ input }: { input: ReportPdfInput }) {
  const prepared = input.preparedFor
    ? `Prepared for ${input.preparedFor}`
    : "Confidential client report";
  return (
    <Document title={input.title}>
      <Page size="A4" style={styles.page}>
        <Text style={styles.title}>{input.title}</Text>
        <Text style={styles.meta}>{prepared}</Text>
        {input.section_order.map((key) => {
          const value = input.sections[key];
          return (
            <View key={key} style={styles.section} wrap={false}>
              <Text style={styles.heading}>{input.section_titles[key] ?? key}</Text>
              {isListSection(key) ? (
                (Array.isArray(value) ? value : []).map((item, i) => (
                  <View key={i} style={styles.listItem}>
                    <Text style={styles.bullet}>•</Text>
                    <Text style={styles.listText}>{item}</Text>
                  </View>
                ))
              ) : (
                <Text style={styles.paragraph}>{typeof value === "string" ? value : ""}</Text>
              )}
            </View>
          );
        })}
      </Page>
    </Document>
  );
}

export async function downloadReportPdf(input: ReportPdfInput): Promise<void> {
  const blob = await pdf(<ReportDocument input={input} />).toBlob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${input.report_id}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
