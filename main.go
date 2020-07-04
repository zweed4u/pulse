package main

import (
	"encoding/json"
	"encoding/xml"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path/filepath"
)

const Config = "config.json"

type Urls struct {
	XMLName xml.Name
	Urls    []Url `xml:"url"`
}

type Url struct {
	XMLName    xml.Name
	Loc        string `xml:"loc"`
	Lastmod    string `xml:"lastmod"`
	ChangeFreq string `xml:"changefreq"`
	Image      Image  `xml:"image"`
}

type Image struct {
	XMLName      xml.Name
	ImageLoc     string `xml:"loc"`
	ImageTitle   string `xml:"title"`
	ImageCaption string `xml:"caption"`
}

type PulseConfig struct {
	SlackWebHook string `json:"slack-webhook-url"`
}

func main() {
	urlPtr := flag.String("base-url", "", "base url for shopify website ie. \"a7.co\", \"us.bape.com\"")
	//productPtr := flag.String("keyword", "", "search keyword for desired product ie. \"cap\", \"striped\"")
	//pollPtr := flag.Int("poll", 10, "poll duration for sitemap refresh sweeps")
	flag.Parse()

	log.Println(*urlPtr)
	dir, err := filepath.Abs(filepath.Dir(os.Args[0]))
	if err != nil {
		log.Fatal(err)
	}
	log.Println(dir)
	configPath := fmt.Sprintf("%s/%s", dir, Config)
	log.Println(configPath)

	// make sure file exists
	var fileExists bool
	info, err := os.Stat(configPath)
	if os.IsNotExist(err) {
		fileExists = false
	} else {
		fileExists = !info.IsDir()
	}

	log.Println(fileExists)
	// read in the config
	if fileExists {
		jsonFile, err := os.Open(configPath)
		if err != nil {
			log.Fatal(err)
		}
		content, err := ioutil.ReadAll(jsonFile)
		if err != nil {
			log.Fatal(err)
		}
		// parse json here
		var config PulseConfig
		// unmarshal it
		err = json.Unmarshal(content, &config)
		if err != nil {
			fmt.Println("error:", err)
		}
		log.Println(config.SlackWebHook)
	}

	productCatalog := make(map[string]string)
	resp, err := http.Get("http://a7.co/sitemap_products_1.xml?from=1&to=9999999999999")
	if err != nil {
		log.Fatalln(err)
	}

	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Fatalln(err)
	}
	sitemapProductsXML := string(body)
	//fmt.Println(sitemapProductsXML)

	// string to bytes array
	byteValue := []byte(sitemapProductsXML)
	var urls Urls
	xml.Unmarshal(byteValue, &urls)
	for i := 0; i < len(urls.Urls); i++ {
		if i == 0 {
			// filter out root node of xml
			// url only contains url and change freq
			continue
		}
		productUrl := urls.Urls[i].Loc
		productName := urls.Urls[i].Image.ImageTitle
		productCatalog[productName] = productUrl
	}
	// remove this later - just for printing
	for name, url := range productCatalog {
		fmt.Printf("%s :: %s\n", name, url)
	}
	fmt.Printf("%d items cataloged\n", len(productCatalog))
}
