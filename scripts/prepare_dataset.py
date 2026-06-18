import pandas as pd
import urllib.request
import os
import glob
from io import StringIO

def main():
    print("Mendownload dataset SMS Spam...")
    url = "https://raw.githubusercontent.com/Andikazidanef15/Sentiment-Analysis-on-Indonesian-SMS-Dataset/main/dataset_sms_spam_v1.csv"
    req = urllib.request.urlopen(url)
    csv_data = req.read().decode('utf-8')
    
    # Read SMS dataset
    df_sms = pd.read_csv(StringIO(csv_data))
    
    # Filter SMS dataset: 0 = Normal (Valid), 1 = Fraud (Penipuan), 2 = Promo (Discard)
    df_sms_filtered = df_sms[df_sms['label'].isin([0, 1])].copy()
    
    # Map labels: 0 -> Valid, 1 -> Penipuan
    def map_sms_label(x):
        return "Valid" if x == 0 else "Penipuan"
        
    df_sms_filtered['final_label'] = df_sms_filtered['label'].apply(map_sms_label)
    df_sms_filtered = df_sms_filtered.rename(columns={'Teks': 'text'})
    df_sms_final = df_sms_filtered[['text', 'final_label']]
    print(f"Berhasil memuat {len(df_sms_final)} baris data SMS (Valid & Penipuan).")

    # Read Kaggle Cleaned Datasets
    print("\nMemproses dataset berita Kaggle (Cleaned)...")
    kaggle_files = glob.glob(os.path.join("dataset", "kaggle", "Cleaned", "*.xlsx"))
    
    kaggle_dfs = []
    for file in kaggle_files:
        print(f"Membaca {os.path.basename(file)}...")
        df_k = pd.read_excel(file)
        
        # Make sure the columns exist
        text_col = 'text_new' if 'text_new' in df_k.columns else 'FullText'
        label_col = 'hoax'
        
        # We need to map hoax: 0 -> Valid, 1 -> Hoax
        def map_kaggle_label(x):
            try:
                val = int(x)
                return "Hoax" if val == 1 else "Valid"
            except:
                return "Valid" # fallback
                
        df_temp = df_k[[text_col, label_col]].copy()
        df_temp['final_label'] = df_temp[label_col].apply(map_kaggle_label)
        df_temp = df_temp.rename(columns={text_col: 'text'})
        df_temp = df_temp[['text', 'final_label']]
        
        # drop na
        df_temp = df_temp.dropna()
        kaggle_dfs.append(df_temp)
        
    if kaggle_dfs:
        df_kaggle_all = pd.concat(kaggle_dfs, ignore_index=True)
        print(f"Berhasil memuat {len(df_kaggle_all)} baris data Berita Kaggle (Valid & Hoax).")
    else:
        df_kaggle_all = pd.DataFrame(columns=['text', 'final_label'])
        print("Dataset Kaggle tidak ditemukan.")

    # Combine All
    print("\nMenggabungkan dataset...")
    df_final = pd.concat([df_kaggle_all, df_sms_final], ignore_index=True)
    
    # Save to CSV (Original Imbalanced)
    output_path = os.path.join("dataset", "final_dataset.csv")
    df_final.to_csv(output_path, index=False)
    print(f"\nSelesai! Dataset akhir (asli) disimpan di {output_path}")
    print("Distribusi Label Asli:")
    print(df_final['final_label'].value_counts())
    
    # --- UNDERSAMPLING (BALANCING) ---
    print("\nMembuat versi dataset seimbang (Balanced Dataset)...")
    # Cari jumlah data dari kelas yang paling sedikit
    min_count = df_final['final_label'].value_counts().min()
    
    # Ambil sampel sebanyak min_count untuk setiap kelas
    df_balanced = df_final.groupby('final_label').sample(n=min_count, random_state=42).reset_index(drop=True)
    
    # Simpan dataset yang sudah seimbang
    balanced_output_path = os.path.join("dataset", "final_dataset_balanced.csv")
    df_balanced.to_csv(balanced_output_path, index=False)
    
    print(f"Selesai! Dataset seimbang disimpan di {balanced_output_path}")
    print("Distribusi Label Balanced:")
    print(df_balanced['final_label'].value_counts())

if __name__ == "__main__":
    main()
