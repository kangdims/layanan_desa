import streamlit as st
import datetime
import uuid
# from supabase import create_client # Un-comment jika sudah menyambungkan Supabase

# Config Halaman
st.set_page_config(
    page_title="Pelayanan Publik Desa Tajurhalang",
    page_icon="🏛️",
    layout="centered"
)

# Dummy In-Memory Database (Pengganti Supabase untuk Demo UI)
if "db_pengajuan" not in st.session_state:
    st.session_state.db_pengajuan = {}

# Header
st.image("https://via.placeholder.com/800x150.png?text=Portal+Layanan+Satu+Pintu+Desa+Tajurhalang", use_container_width=True)
st.title("🏛️ Pelayanan Mandiri Warga Desa Tajurhalang")
st.caption("Kecamatan Tajurhalang, Kabupaten Bogor")

# Tabs Navigasi Utama
tab1, tab2 = st.tabs(["📝 Form Pengajuan Surat", "🔍 Cek Status & Cetak Surat"])

# ==========================================
# TAB 1: FORM PENGAJUAN SURAT
# ==========================================
with tab1:
    st.subheader("Buat Permohonan Surat Baru")
    
    # Penanganan Pre-fill Data jika Ajukan Ulang (dari Tab 2)
    prefill = st.session_state.get("prefill_data", {})
    
    with st.form("form_pengajuan_warga", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nik = st.text_input("NIK (16 Digit)", value=prefill.get("nik", ""), max_chars=16)
            nama = st.text_input("Nama Lengkap", value=prefill.get("nama", ""))
        with col2:
            no_hp = st.text_input("No. WhatsApp (Aktif)", value=prefill.get("no_hp", ""), help="Notifikasi status akan dikirim ke nomor ini")
            rt_rw = st.selectbox("RT / RW", ["001/001", "002/001", "001/002", "003/002", "002/005"], index=0)
        
        jenis_surat = st.selectbox(
            "Jenis Layanan Surat",
            [
                "Surat Keterangan Tidak Mampu (SKTM)",
                "Surat Keterangan Usaha (SKU)",
                "Surat Pengantar Nikah",
                "Surat Keterangan Domisili",
                "Izin Peruntukan Penggunaan Tanah (IPPT) Skala Desa"
            ]
        )
        
        alasan = st.text_area("Alasan / Keperluan Permohonan", value=prefill.get("alasan", ""))
        
        st.write("---")
        st.subheader("Opsi Pencetakan Dokumen")
        opsi_cetak = st.radio(
            "Pilih Metode Pengambilan/Pencetakan Surat:",
            ["MANDIRI (Unduh & Cetak Sendiri)", "KANTOR DESA (Dicetak oleh Staf Desa)"],
            help="Batas waktu cetak adalah 7 hari setelah disetujui Kepala Desa."
        )
        
        st.write("---")
        st.subheader("Unggah Berkas Persyaratan (PDF / JPG)")
        file_ktp = st.file_uploader("Unggah Foto KTP", type=["jpg", "jpeg", "png", "pdf"])
        file_kk = st.file_uploader("Unggah Foto Kartu Keluarga (KK)", type=["jpg", "jpeg", "png", "pdf"])
        
        submitted = st.form_submit_button("🚀 Kirim Permohonan Surat")
        
        if submitted:
            if not nik or not nama or not no_hp:
                st.error("⚠️ Harap lengkapi semua data identitas wajib!")
            else:
                # Generate Nomor Tiket Unik
                tiket_id = f"TKT-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
                
                # Simpan ke Database
                st.session_state.db_pengajuan[tiket_id] = {
                    "nik": nik,
                    "nama": nama,
                    "no_hp": no_hp,
                    "rt_rw": rt_rw,
                    "jenis_surat": jenis_surat,
                    "alasan": alasan,
                    "opsi_cetak": "MANDIRI" if "MANDIRI" in opsi_cetak else "KANTOR_DESA",
                    "status": "PENDING_RTRW",
                    "created_at": datetime.datetime.now(),
                    "expired_at": None, # Diisi saat Kades Approve
                    "pdf_url": None
                }
                
                # Clear session state prefill
                if "prefill_data" in st.session_state:
                    del st.session_state["prefill_data"]
                    
                st.success(f"🎉 Pengajuan Berhasil Disimpan!")
                st.info(f"🔑 **Nomor Tiket Anda:** `{tiket_id}`\n\nSimpan nomor tiket ini untuk mengecek status atau mendownload dokumen.")

# ==========================================
# TAB 2: CEK STATUS & CETAK SURAT
# ==========================================
with tab2:
    st.subheader("Lacak & Unduh Surat")
    
    cari_tiket = st.text_input("Masukkan Nomor Tiket Permohonan:", placeholder="Contoh: TKT-20261005-A1B2").strip()
    
    if st.button("🔎 Cek Status"):
        if cari_tiket in st.session_state.db_pengajuan:
            data = st.session_state.db_pengajuan[cari_tiket]
            now = datetime.datetime.now()
            
            # --- LOGIKA KEDALUWARSA OTOMATIS ---
            is_expired = False
            if data["expired_at"] and now > data["expired_at"]:
                data["status"] = "EXPIRED"
                is_expired = True
            
            st.write("---")
            st.markdown(f"### Detail Permohonan: `{cari_tiket}`")
            col_a, col_b = st.columns(2)
            col_a.write(f"**Nama Pemohon:** {data['nama']}")
            col_a.write(f"**Jenis Surat:** {data['jenis_surat']}")
            col_b.write(f"**Opsi Cetak:** {data['opsi_cetak']}")
            col_b.write(f"**Tanggal Pengajuan:** {data['created_at'].strftime('%d %B %Y %H:%M')}")
            
            # Badging Status
            status = data["status"]
            if status == "PENDING_RTRW":
                st.warning("⏳ Status: **Menunggu Verifikasi RT/RW**")
            elif status == "PENDING_DESA":
                st.warning("⏳ Status: **Diproses Staf Desa Tajurhalang**")
            elif status == "PENDING_KADES":
                st.warning("⏳ Status: **Menunggu Tanda Tangan Digital Kepala Desa**")
            elif status == "COMPLETED" and not is_expired:
                st.success("✅ Status: **Surat Selesai & Siap Dicetak**")
                
                batas_waktu = data["expired_at"].strftime('%d %B %Y pukul %H:%M WIB')
                st.info(f"⏰ **Batas Waktu Cetak:** {batas_waktu}")
                
                if data["opsi_cetak"] == "MANDIRI":
                    # Simulated Download Button PDF
                    st.download_button(
                        label="📄 Unduh Surat Resmi (PDF)",
                        data=b"DUMMY_PDF_CONTENT_DESA_TAJURHALANG",
                        file_name=f"{data['jenis_surat']}_{data['nama']}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.success("🏬 Silakan datang ke Kantor Desa Tajurhalang dengan menunjukkan Nomor Tiket ini kepada Staf Pelayanan.")
                    
            elif status == "EXPIRED" or is_expired:
                st.error("❌ **STATUS: SURAT KEDALUWARSA / EXPIRED**")
                st.write("Masa berlaku cetak/pengambilan surat ini telah habis. Sesuai ketentuan, dokumen ini batal demi hukum dan Anda harus mengajukan ulang.")
                
                # Tombol Ajukan Ulang Cepat
                if st.button("🔄 Ajukan Ulang dengan Data Ini"):
                    st.session_state["prefill_data"] = {
                        "nik": data["nik"],
                        "nama": data["nama"],
                        "no_hp": data["no_hp"],
                        "alasan": data["alasan"]
                    }
                    st.success("Data lama berhasil dimuat! Silakan buka **Tab 'Form Pengajuan Surat'** untuk meninjau dan mengirim ulang.")
            elif status == "REJECTED":
                st.error("🚫 Status: **Permohonan Ditolak**")
                
        else:
            st.error("❌ Nomor tiket tidak ditemukan. Harap periksa kembali nomor tiket Anda.")