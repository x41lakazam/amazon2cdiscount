import xml.etree.ElementTree as ET
import datetime
from xml import etree
import xmltodict
import json
import jinja2
import setup
import os
import shutil
import csv
import urllib.parse as urlparse

from utils import debugme, join_url
import credentials
from logging_manager import logging_mgr
import api_handler as api
import img_converter
import bad_category_handler as bad_cat



class Brand:
    objects = []

    def __init__(self, name):
        self.name = name
        Brand.objects.append(self)

    def jsonify(self):
        return {'name': self.name}

    @classmethod
    def json_objs(cls):
        return json.dumps([obj.jsonify() for obj in cls.objects])

    @classmethod
    def load_json(cls, d):
        return cls(**json.loads(d))

    @classmethod
    def load_json_list(cls, l):
        for d in json.loads(l):
            cls.load_json(d)


class CategoryTree:
    """
        CategoryTree
        Name	Type	Documentation
        Code	String	Category code.
        Name	String	Category name.
        AllowProductIntegration	Bool	True : the seller has the right on product integration on the category.
        False: the selle has not the right on the category.
        AllowOfferIntegration	Bool	True : the seller has the right on offer integration on the category.
        False: the selle has not the right on the category.
        ChildrenCategoryList	List<CategoryTree>	List of the categories children.
        IsStandardProductKindEligible	Bool	True : the category allows standard products for creation.
        False : the category does not allow standard products for creation.
        IsVariantProductKindEligible	Bool	True : the category allows variant products for creation.
        False : the category does not allow variant products for creation.
        IsEANOptional	Bool	True : the product EAN is optionel.
        False : the product EAN is mandatory.
    """


    def __init__(self,
                AllowOfferIntegration,
                AllowProductIntegration,
                ChildrenCategoryList,
                Code,
                IsEANOptional,
                IsStandardProductKindEligible,
                IsVariantProductKindEligible,
                Name,
                parent_name
                ):

            self.allow_product_integration = AllowOfferIntegration
            self.allow_offer_integration = AllowProductIntegration
            self.children_category_list = ChildrenCategoryList
            self.code = Code
            self.is_ean_optional = IsEANOptional
            self.is_standard_product_kind_eligible = IsStandardProductKindEligible
            self.is_variant_product_kind_eligible = IsVariantProductKindEligible
            self.name = Name
            self.parent_name = parent_name

    @classmethod
    def parse_categories(cls, category_tree, parent_name=None):
        ccl = category_tree['ChildrenCategoryList']

        if not ccl:
            kwargs = {'parent_name': parent_name}
            kwargs.update(category_tree)
            cat = Category(**kwargs)
        else:
            if parent_name is None:
                parent_name = cls.get_parent_ct_name(category_tree)
            nxt = ccl['CategoryTree']
            if type(nxt) == list:
                for ct in nxt:
                    cls.parse_categories(ct, parent_name)
            else:
                cls.parse_categories(nxt, parent_name)

    @classmethod
    def get_parent_ct_name(cls, ct):
        try:
            name = ct['ChildrenCategoryList']['CategoryTree'][0]['Name']
        except:
            return None
        else:
            return name

class Category(CategoryTree):

    objects = []
    code_by_name    = {} # NOT SYNCED WITH DB
    objects_by_name = {}
    objects_by_code = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Category.objects.append(self)
        Category.code_by_name[self.name] = self.code
        Category.objects_by_name[self.name] = self
        Category.objects_by_code[self.code] = self

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    def to_json(self):
        return {
            'AllowOfferIntegration':self.allow_product_integration ,
            'AllowProductIntegration':self.allow_offer_integration ,
            'ChildrenCategoryList':self.children_category_list ,
            'Code':self.code ,
            'IsEANOptional':self.is_ean_optional ,
            'IsStandardProductKindEligible':self.is_standard_product_kind_eligible ,
            'IsVariantProductKindEligible':self.is_variant_product_kind_eligible ,
            'Name':self.name ,
            'parent_name':self.parent_name ,
            }



    @classmethod
    def get_code(cls, name):
        cached_dic = json.load(open(setup.cache_categories_list , 'r', encoding='utf-8'))['data']
        if name not in cached_dic:
            return None
        return cached_dic[name]

    @classmethod
    def remove_duplicates(cls):
        names = []
        new = []

        for obj in cls.objects:
            if obj.name not in names:
                names.append(obj.name)
                new.append(obj)

        cls.objects = new

    @classmethod
    def by_name(cls, name):
        mapped = bad_cat.BadCategoryHandler(name).run()
        if name in cls.objects_by_name:
            return cls.objects_by_name[name]
        elif mapped:
            return cls.objects_by_name[mapped]
        else:
            return None

    @classmethod
    def by_code(cls, code):
        if code in cls.objects_by_code:
            return cls.objects_by_code[code]
        else:
            return None


class ProductModel:

    def __init__(
        self,
        ModelId,
        Name,
        CategoryCode,
        Definition=None,
        Version=None,
        ProductXmlStructure=None,
        VariationValueList=None):

        self.ModelId = ModelId
        self.Name = Name
        self.CategoryCode = CategoryCode
        self.Definition = Definition
        self.Version = Version
        self.ProductXmlStructure = ProductXmlStructure
        self.VariationValueList = VariationValueList

    @classmethod
    def from_dict(cls, dic):
        for k in ['CategoryCode', 'ModelId', 'Name', 'ProductXmlStructure']:
            if k not in dic:
                dic[k] = None

        attrs = {
            'CategoryCode': dic['CategoryCode'],
            'ModelId': dic['ModelId'],
            'Name': dic['Name'],
            'ProductXmlStructure': dic['ProductXmlStructure']
        }

        return cls(**attrs)

    def to_json(self):
        return {
            'ModelId': self.ModelId,
            'Name': self.Name,
            'CategoryCode': self.CategoryCode,
            'Definition': self.Definition,
            'Version': self.Version,
            'ProductXmlStructure': self.ProductXmlStructure,
            'VariationValueList': self.VariationValueList,
        }

    @classmethod
    def from_json(cls, l):
        objs = []
        for dic in l:
            objs.append(cls(**dic))
        return objs


class ModelDefinition:
    def __init__(self,
                ListProperties=None,
                MandatoryModelProperties=None,
                SingleFreeTextProperties=None,
                MultipleFreeTextProperties=None,
                ):

        self.ListProperties = self.parse_list_properties(ListProperties) # Dict of properties
        self.SingleFreeTextProperties = SingleFreeTextProperties
        self.MultipleFreeTextProperties = MultipleFreeTextProperties
        self.MandatoryModelProperties = MandatoryModelProperties

    def parse_list_properties(self, list_properties):
        """
        list_properties: list
        """
        keyvalue = list_properties['a:KeyValueOfstringArrayOfstringty7Ep6D1']
        properties = {}
        for kv_dic in keyvalue:
            key = kv_dic['a:Key']
            value = kv_dic['a:Value']['a:string']
            properties[key] = value

        return properties

    @classmethod
    def from_dict(cls, dic):
        attrs = {
            'ListProperties': dic['ListProperties'],
            'MandatoryModelProperties':dic['MandatoryModelProperties'],
        }

        return cls(**attrs)


class VariationDescription:
    def __init__(self,
        VariantValueId,
        VariantValueDescription
                    ):

        self.VariantValueId = VariantValueId
        self.VariantValueDescription = VariantValueDescription


class ProductPackage:

    def __init__(self, products_and_categories, zipfile_name="auto",
                 tmp_dir_name=".tmp_product", pkg_name='auto'):

        assert len(products_and_categories) != 0, "Products list passed to ProductPackage is empty"

        if pkg_name == 'auto':
            pkg_name = self.get_auto_name()

        self.pkg_name = pkg_name

        if zipfile_name == 'auto':
            zipfile_name = self.pkg_name + '.zip'

        self.products_xml = ProductsXML(products_and_categories, pkg_name=self.pkg_name)

        self.dest_dir = os.path.join(setup.results_path, pkg_name)

        if os.path.exists(self.dest_dir):
            shutil.rmtree(self.dest_dir)
            logging_mgr.ok_msg("Removed old archive", self.dest_dir)

        os.mkdir(self.dest_dir)
        self.url_to_dir = urlparse.urljoin(setup.basedir_url, self.dest_dir)

        # pics
        pics_dir_name = 'images'
        os.mkdir(os.path.join(self.dest_dir, pics_dir_name))
        self.path_to_pics = os.path.join(self.dest_dir, pics_dir_name)
        self.url_to_pics  = urlparse.urljoin(self.url_to_dir, pics_dir_name)

        # tmp dir
        self.tmp_dir_name = tmp_dir_name

        # zipfile
        self.arcname      = os.path.join(self.dest_dir, zipfile_name)
        self.zipfile_url  = join_url(self.url_to_dir, zipfile_name)

        # init
        self.is_submitted   = False
        self.submit_status  = None
        self.pkg_id         = None

    def get_auto_name(self):
        now = datetime.datetime.now()
        name = "Integration-{}-{}-{}-{}-{}".format(now.year, now.month, now.day, now.hour,
                                                   now.minute)
        return name

    def _write_to_file(self, filename, data):
        open(filename, 'w', encoding='utf-8').write(data)

    def _create_tmp_dir(self, dirname=".tmp_to_zip"):

        if os.path.exists(dirname):
            shutil.rmtree(dirname)
        os.mkdir(dirname)

        for sub in ('_rels', 'Content'):
            path = os.path.join(dirname, sub)
            os.mkdir(path)

        contents = {
            os.path.join("_rels",".rels"):self.build_rels(),
            os.path.join("Content", "Products.xml"): self.products_xml.render(basedir=self.dest_dir),
            "[Content_Types].xml": self.build_content_types(),
        }

        for fn, d in contents.items():
            path = os.path.join(dirname, fn)
            open(path, 'w', encoding='utf-8').write(d)

        return True

    def _delete_tmp_dir(self, dirname=".tmp_to_zip"):
        if os.path.exists(dirname):
            shutil.rmtree(dirname)
            return True
        return False

    def create(self):

        logging_mgr.process_msg("Creating package in location <{}> and public url <{}>".format(self.arcname, self.zipfile_url))

        dirname = ".tmp_to_zip"
        self.products_xml.download_all_pics(setup.cache_images_dir)
        self._create_tmp_dir(dirname)
        shutil.make_archive(os.path.splitext(self.arcname)[0], "zip", dirname)
        self._delete_tmp_dir(dirname)

        logging_mgr.ok_msg("Create archive",self.arcname)
        logging_mgr.ok_msg("Deleted temporary directory", dirname)


        return self.arcname

    def build_content_types(self):
        content = """
        <?xml version="1.0" encoding="utf-8"?>
        <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
            <Default Extension="png" ContentType="image/png" />
            <Default Extension="jpg" ContentType="image/jpg" />
            <Default Extension="xml" ContentType="text/xml" />
            <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />
        </Types>
        """
        return content

    def build_rels(self):
        content = """
        <?xml version="1.0" encoding="utf-8"?>

        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">

        <Relationship Type="http://cdiscount.com/uri/document"

        Target="/Content/Products.xml"/>

        </Relationships>
        """
        return content

    # Submit methods
    def soap_request_body(self):
        """
        Builds a string to inject in Soap Action request body
        """
        content = f"""
            <productPackageRequest xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
                <ZipFileFullPath>{self.zipfile_url}</ZipFileFullPath>
            </productPackageRequest>
        """
        return content

    def submit_package(self):
        """
            Use it to submit this package to cdiscount, using SubmitProductPackage throught
            api_handler module
        """

        submit_pkg_action = api.SoapAction.actions['SubmitProductPackage']
        r = submit_pkg_action(credentials.token, body=self.soap_request_body())

        pkg_id = r.sa_result['PackageId']

        self.pkg_id = str(pkg_id)
        self.is_submitted = True

        return pkg_id

    def to_csv(self, csv_outpath=None):
        if csv_outpath is None:
            csv_outpath = os.path.join(self.dest_dir, "output_pkg.csv")
        return self.products_xml.to_csv(csvfilename=csv_outpath)

    def get_submissions_result(self):
        assert self.is_submitted, "Pkg needs to be submitted in order to get submissions result"

        body = """
            <productPackageFilter xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
                <PackageID>{}</PackageID>
            </productPackageFilter>
        """.format(self.pkg_id)
        action = api.SoapAction.actions['GetProductPackageSubmissionResult']
        r = action(credentials.token, body=body)

        if str(self.pkg_id) != str(r.sa_result['PackageId']):
            # Do something if id is different ? If you want to, then put your code here
            pass

        status = r.sa_result['PackageIntegrationStatus']
        self.submit_status = status
        return status


class ProductsXML:

    def __init__(self, products_and_categories, pkg_name='auto'):
        """
            products is a list of tuples (AmazonProduct, Category)
            Building package that has to be sent in SubmitProductPackage function, combining
            ProductPackage objects
        """
        if pkg_name == 'auto':
            pkg_name = self.get_auto_name()

        self.pkg_name = pkg_name
        self.product_pkgs = [ProductXML(*pnc) for pnc in products_and_categories]

    def download_all_pics(self, dest):
        logging_mgr.process_msg('Downloading & converting product pictures to', dest)
        for product in self.product_pkgs:
            product.download_pictures(dest)

    def get_auto_name(self):
        now = datetime.datetime.now()
        name = "Integration-{}-{}-{}-{}-{}".format(now.year, now.month, now.day, now.hour,
                                                   now.minute)
        return name

    def render(self, basedir='.'):
        """
        Transform allthe product package objects to one big xml
        """
        template_filename   = "templates/products.xml"
        template_content    = open(template_filename, 'r', encoding='utf-8').read()
        template            = jinja2.Template(template_content)
        rendered            = template.render(pkg_name=self.pkg_name, product_pkgs=self.product_pkgs)

        return rendered

    def to_csv(self, csvfilename="out.csv"):

        cols = {
            'ref':'Référence vendeur',
            'ean':'EAN (Facultatif pour Mode et Maison)',
            'marque':'Marque',
            'nature':'Nature du produit',
            'category code': 'Code catégorie',
            'lib court':'Libellé court panier',
            'lib long': 'Libellé long produit',
            'description':'Description produit',
            'img1': 'Image 1 (jpeg)',
            'sku': 'Sku famille',
            'taille': 'Taille (borné)',
            'couleur marketing':'Couleur marketing',
            'description marketing':'Description marketing',
            'img2': 'Image 2 (jpeg)',
            'img3': 'Image 3 (jpeg)',
            'img4': 'Image 4 (jpeg)',
            'navigation':'Navigation / classification / rayon',
            'isbn':"ISBN",
            'mfpn': 'MFPN',
            'longueur': 'Longueur (cm)',
            'largeur': 'Largeur (cm)',
            'hauteur': 'Hauteur (cm)',
            'poids': 'Poids (kg)',
            'avertissements': 'Avertissement(s)',
            'commentaire':'Commentaire',
            'couleurs':'couleur(s)',
            'couleur principale':'Couleur principale',
            'genre': 'Genre',
            'licence': 'Licence',
            'sports': 'Sports',
            'type de public': 'Type de public',
        }

        fieldsnames = cols.values()

        with open(csvfilename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL,
                                fieldnames=fieldsnames)

            writer.writeheader()
            for pkg in self.product_pkgs:
                writer.writerow(pkg.to_csv())

        return csvfilename



class ProductXML:

    def __init__(self, amazon_product, category):
        """
            <Product> Tag in ProductsPackage
        """
        self.amazon_product = amazon_product
        self.category       = category
        self.bad_urls       = []

    def get_pictures_xml(self):
        """
            A part of the xml is related to pictures, I generate this part here with a for loop
        """
        xml = """
				<Product.Pictures>
                    {}
				</Product.Pictures>
        """

    def get_pictures_remote_urls(self):

        pictures_uri = self.amazon_product['imagesCSV'].split(',') # Test unit: pictures are uri separated with a ,
        pictures_url = ["https://images-na.ssl-images-amazon.com/images/I/"+uri for uri in pictures_uri]

        while len(pictures_url) < 4:
            pictures_url.append('')

        return pictures_url[:4]

    def get_pictures_local_urls(self):
        pictures_uri = self.amazon_product['imagesCSV'].split(',') # Test unit: pictures are uri separated with a ,
        pictures_url = [urlparse.urljoin(setup.cache_images_dir_url, uri) for uri in pictures_uri]

        while len(pictures_url) < 4:
            pictures_url.append('')

        return pictures_url[:4]

    def download_pictures(self, dest):

        urls = self.get_pictures_remote_urls()

        for url in urls:
            name = url.split('/')[-1]
            if not url:
                continue
            filepath = os.path.join(dest, name)
            if os.path.exists(filepath):
                continue
            img_converter.download_img(url, filepath)
            img_name = img_converter.jpg_to_jpeg(filepath)
            if os.path.getsize(img_name) == 0:
                self.bad_urls.append(url)
                logging_mgr.err_msg("Bad image url: {}".format(url), verbose_lvl=4)
            else:
                logging_mgr.ok_msg("Downloaded image from {}".format(url), verbose_lvl=4)



    def render(self):
        """
        sellerproductid = ean
        Brandname = manufacturer
        ProductKind = "Standard"
        CategoryCode = Id category cdiscount
        LongLabel = title
        Description = description + features
        SellerProductFamily= on ne l'utilise pas vu que nos produit sont "Standard"
        Size= on ne l'utilise pas vu que nos produit sont "Standard"
        SellerProductColorName = on ne l'utilise pas vu que nos produit sont "Standard"
        Model = "0"
        Navigation = CategoryTreeName
        """

        create_model_property = lambda keyvaluetuple: '<x:String x:Key="{}">{}</x:String>'.format(keyvaluetuple[0], keyvaluetuple[1])

        p = self.amazon_product
        description = self.amazon_product['description'] + self.amazon_product['features']
        brandName   = "Aucune" #TODO

        # Generate product.ModelProperty
        model_properties_raw = [
            #("brand", self.amazon_product["brand"]),
            #("model", self.amazon_product["model"]),
            #("size", self.amazon_product["size"]),
            #("edition", self.amazon_product["edition"]),
            #("format", self.amazon_product["format"]),
            #("Height", self.amazon_product["packageHeight"] + ' cm'),
            #("Length", self.amazon_product["packageLength"] + ' cm'),
            #("Width", self.amazon_product["packageWidth"] + ' cm'),
            #("Weight", self.amazon_product["packageWeight"] + ' kg'),
            # Short label, shortproductid, sellerproductfamily
            ("Couleur principale", self.amazon_product["color"]),
            ("Genre", self.amazon_product["genre"]),
        ]

        ModelProperties = '\n'.join([create_model_property(tup) for tup in model_properties_raw if
                                     tup[1]])

        # Generate others
        ProductType = self.amazon_product["type"].replace('_', ' ')
        SellerProductId=self.amazon_product['ean']
        BrandName=brandName
        ProductKind="Standard"
        CategoryCode=self.category.code
        ShortLabel=self.category
        LongLabel=self.amazon_product['title']
        Description=description
        if not Description:
            Description = LongLabel
        SellerProductFamily=""
        Size=""
        SellerProductColorName=""
        Model="SOUMISSION CREATION PRODUIT_MK"
        Navigation=self.category.parent_name

        # There are several images, so i generate all the code in a list and join it with a '\n', i
        # also remove every picture contained in bad_urls, meaning that the file is empty
        pictures_url = [url for url in self.get_pictures_local_urls() if url not in self.bad_urls]
        pictures_xml = '\n'.join(['<ProductImage Uri="{}" />'.format(url) for url in pictures_url if url])

        xml = f"""
			<Product BrandName="{BrandName}" CategoryCode="{CategoryCode}" \
            Description="{Description}" LongLabel="{LongLabel}" Model="{Model}" \
            Navigation="{Navigation}" ProductKind="Standard" SellerProductId="{SellerProductId}" \
            ShortLabel="{ShortLabel}">
				<Product.EanList>
					<ProductEan Ean="{SellerProductId}"/>
				</Product.EanList>
            """
        if len(ModelProperties):
            xml += f"""
                <Product.ModelProperties>
                    {ModelProperties}
                </Product.ModelProperties>
                """

        xml += f"""
				<Product.Pictures>
                    {pictures_xml}
				</Product.Pictures>
			</Product>
        """

        return xml

    def to_csv(self):
        """
        sellerproductid = ean
        Brandname = manufacturer
        ProductKind = "Standard"
        CategoryCode = Id category cdiscount
        LongLabel = title
        Description = description + features
        SellerProductFamily= on ne l'utilise pas vu que nos produit sont "Standard"
        Size= on ne l'utilise pas vu que nos produit sont "Standard"
        SellerProductColorName = on ne l'utilise pas vu que nos produit sont "Standard"
        Model = "0"
        Navigation = CategoryTreeName
        """

        cols = {
            'ref':'Référence vendeur',
            'ean':'EAN (Facultatif pour Mode et Maison)',
            'marque':'Marque',
            'nature':'Nature du produit',
            'category code': 'Code catégorie',
            'lib court':'Libellé court panier',
            'lib long': 'Libellé long produit',
            'description':'Description produit',
            'img1': 'Image 1 (jpeg)',
            'sku': 'Sku famille',
            'taille': 'Taille (borné)',
            'couleur marketing':'Couleur marketing',
            'description marketing':'Description marketing',
            'img2': 'Image 2 (jpeg)',
            'img3': 'Image 3 (jpeg)',
            'img4': 'Image 4 (jpeg)',
            'navigation':'Navigation / classification / rayon',
            'isbn':"ISBN",
            'mfpn': 'MFPN',
            'longueur': 'Longueur (cm)',
            'largeur': 'Largeur (cm)',
            'hauteur': 'Hauteur (cm)',
            'poids': 'Poids (kg)',
            'avertissements': 'Avertissement(s)',
            'commentaire':'Commentaire',
            'couleurs':'couleur(s)',
            'couleur principale':'Couleur principale',
            'genre': 'Genre',
            'licence': 'Licence',
            'sports': 'Sports',
            'type de public': 'Type de public',
        }

        pictures_url = self.get_pictures_local_urls()
        description = self.amazon_product['description'] + self.amazon_product['features']

        values = {
            'ref':'36319',
            'ean':self.amazon_product['ean'],
            'marque':self.amazon_product['manufacturer'],
            'nature':'standard',
            'category code':self.category.code,
            'lib court':self.amazon_product['title'],
            'lib long':self.amazon_product['title'],
            'description':description,
            'img1':pictures_url[0],
            'sku':'',
            'taille':'',
            'couleur marketing':'',
            'description marketing':'',
            'img2':pictures_url[1],
            'img3':pictures_url[2],
            'img4':pictures_url[3],
            'navigation':self.category.parent_name,
            'isbn':'',
            'mfpn':'',
            'longueur':self.amazon_product['packageLength'],
            'largeur':self.amazon_product['packageWidth'],
            'hauteur':self.amazon_product['packageHeight'],
            'poids':self.amazon_product['packageWeight'],
            'avertissements':'',
            'commentaire':'',
            'couleurs':'',
            'couleur principale':self.amazon_product['color'],
            'genre':'',
            'licence':'',
            'sports':'',
            'type de public':'',
        }

        corr = {cols[k]: values[k] for k in cols}
        return corr







